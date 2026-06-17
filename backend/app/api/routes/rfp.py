import json
from pydoc import text
import shutil
import sqlite3

from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, UploadFile, File

from app.services.analysis_orchestrator import run_analysis
from app.services.executive_brief import generate_executive_brief
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from app.db.database import SessionLocal
from app.models.chat_message import ChatMessage

from app.services.pdf_parser import (
    extract_text_from_pdf,
    extract_documents_from_pdf,
)
from app.services.ocr_service import extract_text_with_ocr
from app.services.chunker import chunk_document
from app.services.async_processor import process_chunks_async
from app.services.merger import merge_results
from app.services.aggregator import aggregate_results
from app.services.confidence import add_confidence_scores
from app.services.vector_store import create_vector_store, search_vector_store

from app.services.chat_rag import (
    chat_with_rfp,
    stream_chat_with_rfp,
    generate_document_summary,
)
from app.services.chat_memory import (
    get_chat_history,
    create_session,
    get_all_sessions,
    delete_session,
    delete_all_sessions,
    rename_session,
)
from app.db.document_store import save_document

from app.db.document_store import (
    save_document,
    get_save_documents,
    get_documents_by_session,
    get_document,
    delete_document as delete_document_db,
    delete_documents_by_session,
)
from app.services.export_service import generate_docx_report, generate_pdf_report
from app.services.context_memory import save_context
from app.services import report_store
from app.services.rfp_extractor import extract_rfp_metadata
from app.services.compliance_matrix import generate_compliance_matrix

from app.services.solicitation_classifier import classify_solicitation
from app.services.proposal_strategy import generate_strategy


from langchain_core.documents import Document
from app.db.chunk_store import save_chunks, get_chunks, delete_chunks
import uuid

from app.services.vector_store import delete_vector_store_for_session
from app.services.master_extractor import build_procurement_kb
from app.services.procurement_kb import build_procurement_kb
from app.services.opportunity_assessment import assess_opportunity

# -----------------------------------
# Router
# -----------------------------------
router = APIRouter(prefix="", tags=["RFP"])

UPLOAD_DIR = "uploads"
Path(UPLOAD_DIR).mkdir(exist_ok=True)


# -----------------------------------
# Upload + Process RFP
# -----------------------------------
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}


async def _check_upload_cancelled(job_id: str) -> bool:
    from app.db.document_store import get_upload_job

    job = get_upload_job(job_id)
    return bool(job and job.get("status") == "cancelled")


async def process_upload_job(
    *, job_id: str, session_id: str, file_path: str, original_filename: str
) -> None:
    """Background job runner.

    Cancellation is cooperative: we check job status before embedding/chunk persistence and before report persistence.
    """

    try:
        if await _check_upload_cancelled(job_id):
            return

        # Extract PDF text
        text = extract_text_from_pdf(str(file_path))

        if await _check_upload_cancelled(job_id):
            return

        # OCR fallback
        if len(text.strip()) < 500:
            print("Low text detected. Running OCR...")
            text = extract_text_with_ocr(str(file_path))

        if await _check_upload_cancelled(job_id):
            return

        # Extract page-aware documents
        documents = extract_documents_from_pdf(str(file_path))

        # Chunk document
        chunks = chunk_document(documents)
        print("SESSION:", session_id)
        print("CHUNKS CREATED:", len(chunks))

        # Generate executive summary (CPU/LLM independent)
        document_summary = generate_document_summary(text)

        # IMPORTANT: cancellation checks BEFORE persisting embeddings/chunks/report
        if await _check_upload_cancelled(job_id):
            return

        # Store embeddings (this is the main side-effect to avoid on cancel)
        create_vector_store(session_id=session_id, chunks=chunks)
        print("VECTOR STORE CREATED")

        if await _check_upload_cancelled(job_id):
            return

        # Generate structured procurement extraction
        print("STARTING RFP EXTRACTION...")
        structured_data = extract_rfp_metadata(text)
        # Defensive: ensure structured_data is a dict before accessing keys
        solicitation_type = ""
        if isinstance(structured_data, dict):
            solicitation_type = structured_data.get("solicitation_type", "") or ""
        # Ensure we slice a string, not something else
        if isinstance(solicitation_type, str):
            print(
                "RFP EXTRACTION DONE:",
                solicitation_type[:50] if solicitation_type else "empty",
            )
        else:
            print("RFP EXTRACTION DONE: type unexpected")

        # Analysis
        print("STARTING ANALYSIS...")
        analysis = run_analysis(text)
        print("ANALYSIS DONE")
        classification = analysis["classification"]
        strategy = analysis["strategy"]

        print("BUILDING PROCUREMENT KB...")
        procurement_kb = build_procurement_kb(
            text=text,
            structured_data=structured_data,
            classification=classification,
            strategy=strategy,
        )
        print("PROCUREMENT KB DONE")
        legacy_compliance_matrix = analysis["compliance"]

        # Use analysis compliance directly (skip slow extra LLM call)
        compliance_matrix = legacy_compliance_matrix

        # Skip slow executive brief + opportunity calls (they hang)
        # Report already has analysis data from earlier steps
        print("SKIPPING SLOW EXECUTIVE BRIEF + OPPORTUNITY")
        executive_brief = "Analysis complete"
        opportunity_assessment = {"error": "skipped"}

        if await _check_upload_cancelled(job_id):
            return

        # Skip chunk processing - redundant after all other analysis
        merged = {}  # Empty dict, not list
        aggregated = aggregate_results(merged)

        # Add summary
        aggregated["summary"] = [{"value": document_summary}]
        aggregated["executive_brief"] = executive_brief
        aggregated["structured_data"] = structured_data
        aggregated["compliance_matrix"] = compliance_matrix
        aggregated["classification"] = classification
        aggregated["proposal_strategy"] = strategy
        aggregated["executive_brief"] = executive_brief
        aggregated["opportunity_assessment"] = opportunity_assessment
        aggregated["procurement_kb"] = procurement_kb

        # Add confidence scores
        aggregated["scope_of_work"] = add_confidence_scores(
            aggregated.get("scope_of_work", [])
        )
        aggregated["deadlines"] = add_confidence_scores(aggregated.get("deadlines", []))
        aggregated["staffing_requirements"] = add_confidence_scores(
            aggregated.get("staffing_requirements", [])
        )
        aggregated["compliance_items"] = add_confidence_scores(
            aggregated.get("compliance_items", [])
        )

        # Cancellation check BEFORE persisting memory/report/document/chunks
        if await _check_upload_cancelled(job_id):
            return

        # Save context memory
        from app.services.context_memory import save_context

        save_context(
            session_id=session_id, context_type="summary", content=document_summary
        )
        save_context(
            session_id=session_id,
            context_type="document_name",
            content=original_filename,
        )
        save_context(
            session_id=session_id,
            context_type="upload_time",
            content=str(datetime.now()),
        )

        save_context(
            session_id=session_id,
            context_type="important_points",
            content=f"""
    Scope:
    {aggregated.get('scope_of_work', [])}

    Deadlines:
    {aggregated.get('deadlines', [])}

    Compliance:
    {aggregated.get('compliance_items', [])}
    """,
        )

        save_context(
            session_id=session_id,
            context_type="structured_extraction",
            content=json.dumps(structured_data, default=str),
        )

        save_context(
            session_id=session_id,
            context_type="compliance_matrix",
            content=json.dumps(compliance_matrix, default=str),
        )

        report_store.save_report(session_id, aggregated)

        if await _check_upload_cancelled(job_id):
            return

        # Store report/document/chunks - wrap in try to ensure it saves
        try:
            print("TRYING TO SAVE DOCUMENT...")
            print(f"  session_id: {session_id}")
            print(f"  filename: {original_filename}")
            print(f"  procurement_kb type: {type(procurement_kb)}")
            print(f"  executive_brief type: {type(executive_brief)}")
            print(f"  opportunity_assessment type: {type(opportunity_assessment)}")

            document_id = save_document(
                session_id=session_id,
                filename=original_filename,
                pdf_path=str(file_path),
                summary=document_summary,
                structured_data=structured_data,
                compliance_matrix=compliance_matrix,
                classification=classification,
                proposal_strategy=strategy,
                executive_brief=executive_brief,
                opportunity_assessment=opportunity_assessment,
                procurement_kb=procurement_kb,
            )
            print(f"DOCUMENT SAVED WITH ID: {document_id}")
            save_chunks(document_id=document_id, chunks=chunks)

            # IMPORTANT: mark job completed immediately after save succeeds
            from app.db.document_store import set_upload_job_status

            set_upload_job_status(job_id, "completed")
            print(f"UPLOAD JOB {job_id} COMPLETED")
        except Exception as e:
            print(f"SAVE DOCUMENT ERROR: {e}")
            import traceback

            traceback.print_exc()
            # Try still to save report even if doc save fails
            document_id = None

    except Exception as e:
        print(f"Upload job {job_id} failed: {e}")
    finally:
        # If the job was cancelled, best-effort cleanup: do not persist anything further.
        try:
            from app.db.document_store import set_upload_job_status
            from app.db.document_store import set_upload_job_cancelled

            # If cancelled, ensure status stays cancelled.
            job = None
            from app.db.document_store import get_upload_job

            job = get_upload_job(job_id)
            if job and job.get("status") == "cancelled":
                # Best-effort: delete uploaded file so user doesn't see it later.
                try:
                    Path(file_path).unlink(missing_ok=True)
                except Exception:
                    pass
            else:
                set_upload_job_status(job_id, "completed")
        except Exception:
            pass


@router.post("/upload")
async def upload_rfp(session_id: str, file: UploadFile = File(...)):
    # Validate supported formats early
    filename = (file.filename or "").strip()
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return {
            "error": "Unsupported format. Please upload a PDF or DOC/DOCX file.",
            "unsupported_filename": filename,
            "unsupported_extension": ext,
        }, 400

    # Create cancellable upload job
    job_id = str(uuid.uuid4())
    unique_name = f"{job_id}_{file.filename}"
    file_path = Path(UPLOAD_DIR) / unique_name

    from app.db.document_store import create_upload_job

    create_upload_job(
        job_id=job_id,
        session_id=session_id,
        filename=file.filename,
        pdf_path=str(file_path),
    )

    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Background processing so cancellation can take effect before embeddings/report persistence
    import asyncio

    asyncio.create_task(
        process_upload_job(
            job_id=job_id,
            session_id=session_id,
            file_path=str(file_path),
            original_filename=file.filename,
        )
    )

    return {"job_id": job_id, "session_id": session_id}


@router.get("/upload/{job_id}")
async def get_upload_job_status(job_id: str):
    from app.db.document_store import get_upload_job

    return get_upload_job(job_id)


@router.post("/upload/{job_id}/cancel")
async def cancel_upload_job(job_id: str):
    from app.db.document_store import set_upload_job_cancelled

    status = set_upload_job_cancelled(job_id)
    if not status:
        return {"error": "Job not found"}, 404
    return {"job_id": job_id, "status": status}


# -----------------------------------
# Get Documents
# -----------------------------------
@router.get("/documents")
async def get_documents(session_id: str = ""):
    if session_id:
        return {"documents": get_documents_by_session(session_id)}
    return {"documents": get_save_documents()}


@router.get("/documents/{document_id}")
async def get_document_by_id(document_id: int):

    document = get_document(document_id)

    if not document:
        return {"error": "Document not found"}

    # ==========================
    # Rebuild Vector Store
    # ==========================

    stored_chunks = get_chunks(document_id)

    documents = []

    for page, content, metadata in stored_chunks:

        documents.append(Document(page_content=content, metadata=json.loads(metadata)))

    if documents:
        create_vector_store(session_id=document["session_id"], chunks=documents)

    report = {
        "summary": document["summary"],
        "structured_data": document["structured_data"],
        "compliance_matrix": document["compliance_matrix"],
        "classification": document["classification"],
        "proposal_strategy": document["proposal_strategy"],
        "executive_brief": document["executive_brief"],
        "procurement_kb": document["procurement_kb"],
        "opportunity_assessment": document.get("opportunity_assessment", {}),
    }

    return {
        "document": document,
        "report": report,
        "session_id": document["session_id"],
    }


@router.delete("/documents")
async def clear_documents(session_id: str = ""):
    """Clear persisted PDF/document history. If session_id provided, only clear that session's docs."""

    # 1) Delete PDF files on disk (only matching session if session_id provided)
    uploads = Path("uploads")
    if uploads.exists():
        for p in uploads.iterdir():
            if p.is_file() and p.suffix.lower() == ".pdf":
                # If session_id provided, only delete files for that session
                if session_id and session_id not in p.name:
                    continue
                p.unlink(missing_ok=True)

    # 2) Wipe DB rows (documents + chunks) - session-specific if session_id provided
    if session_id:
        # Delete only this session's docs
        delete_documents_by_session(session_id)
        try:
            from app.db.chunk_store import delete_chunks
            import sqlite3

            conn = sqlite3.connect("documents.db", timeout=5.0)
            try:
                conn.execute(
                    "DELETE FROM document_chunks WHERE document_id IN (SELECT id FROM documents WHERE session_id = ?)",
                    (session_id,),
                )
                conn.commit()
            finally:
                conn.close()
        except Exception:
            pass
    else:
        # Clear everything (legacy behavior)
        try:
            import sqlite3

            conn = sqlite3.connect("documents.db", timeout=5.0)
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("DELETE FROM document_chunks")
                conn.execute("DELETE FROM documents")
                conn.commit()
            finally:
                conn.close()
        except Exception:
            pass

    # 3) Wipe Chroma persisted collections - session-specific if session_id provided
    chroma_root = Path("chroma_db")
    if chroma_root.exists():
        for child in chroma_root.iterdir():
            if child.is_dir():
                if session_id:
                    # Only delete if folder matches session_id
                    if session_id not in child.name:
                        continue
                shutil.rmtree(child, ignore_errors=True)

    return {"message": "PDF history cleared"}


@router.delete("/documents/{document_id}")
async def delete_document(document_id: int):

    document = get_document(document_id)

    if not document:
        return {"error": "Document not found"}

    # We need session_id before deleting DB rows.
    session_id = document.get("session_id")

    pdf_path = Path(document["pdf_path"])

    if pdf_path.exists():
        pdf_path.unlink()

    delete_chunks(document_id)
    delete_document_db(document_id)

    # Permanently delete vector store so deleted PDFs never re-appear after refresh.
    try:
        if session_id:
            delete_vector_store_for_session(str(session_id))
    except Exception:
        pass

    return {"message": "Document deleted"}


# -----------------------------------
# Delete Document by Filename
# -----------------------------------
@router.delete("/documents-by-filename/{filename}")
async def delete_document_by_filename(filename: str):
    """Delete a document by its filename (for frontend compatibility)."""
    import urllib.parse
    import time

    decoded_filename = urllib.parse.unquote(filename)

    # Use retry logic to handle locked database
    document_id = None
    pdf_path = None

    for attempt in range(3):
        try:
            with sqlite3.connect("documents.db", timeout=5.0) as conn:
                cursor = conn.execute(
                    "SELECT id, pdf_path FROM documents WHERE filename = ?",
                    (decoded_filename,),
                )
                row = cursor.fetchone()

                if not row:
                    return {"error": "Document not found"}

                document_id, pdf_path = row[0], row[1]
                break
        except sqlite3.OperationalError:
            if attempt < 2:
                time.sleep(0.5)
            else:
                return {"error": "Database busy, please try again"}

    if not document_id:
        return {"error": "Document not found"}

    # Delete from database
    try:
        delete_chunks(document_id)
    except Exception:
        pass

    try:
        delete_document_db(document_id)
    except Exception:
        pass

    # IMPORTANT: Permanently delete vector store for the owning session.
    # This prevents deleted documents from showing up in future retrieval/search.
    try:
        with sqlite3.connect("documents.db", timeout=5.0) as conn:
            row = conn.execute(
                "SELECT session_id FROM documents WHERE id = ?",
                (document_id,),
            ).fetchone()
        # If DB row is already deleted above, this can be None; in that case
        # we fallback to deleting by the provided filename's last known session is not possible.
        if row and row[0]:
            delete_vector_store_for_session(str(row[0]))
    except Exception:
        pass

    # Delete PDF file if exists
    try:
        pdf_path_obj = Path(pdf_path)
        if pdf_path_obj.exists():
            pdf_path_obj.unlink()
    except Exception:
        pass

    return {"message": "Document deleted"}


@router.get("/report")
async def get_report(session_id: str):
    report = report_store.get_report(session_id)
    if not report:
        return {"error": "No report available. Upload an RFP first."}
    return report


# -----------------------------------
# Semantic Search API
# -----------------------------------
@router.get("/search")
async def search_rfp(session_id: str, query: str):
    # NOTE: existing search_vector_store uses global session store.
    results = search_vector_store(session_id=session_id, query=query)
    return {
        "query": query,
        "results": [
            {"page": doc.metadata.get("page"), "content": doc.page_content}
            for doc in results
        ],
    }


# -----------------------------------
# Normal Chat API
# -----------------------------------
@router.get("/chat")
async def chat_rfp(session_id: str, question: str):
    return chat_with_rfp(session_id, question)


# -----------------------------------
# Streaming Chat API
# -----------------------------------
@router.get("/stream-chat")
async def stream_chat(session_id: str, question: str):
    return await stream_chat_with_rfp(session_id, question)


# -----------------------------------
# Export DOCX
# -----------------------------------
@router.get("/export-docx")
async def export_docx(session_id: str):
    report = report_store.get_report(session_id)
    if not report:
        return {"error": "No report found"}

    file_path = generate_docx_report(report)
    return FileResponse(path=file_path, filename="rfp_report.docx")


# -----------------------------------
# Export PDF
# -----------------------------------
@router.get("/export-pdf")
async def export_pdf(session_id: str):
    report = report_store.get_report(session_id)
    if not report:
        return {"error": "No report found"}

    file_path = generate_pdf_report(report)
    return FileResponse(path=file_path, filename="rfp_report.pdf")


# -----------------------------------
# Clear Chat History
# -----------------------------------
@router.get("/chat-history")
async def chat_history(session_id: str):
    return {"messages": get_chat_history(session_id)}


@router.get("/chat-history/{session_id}")
async def get_history(session_id: str):

    history = get_chat_history(session_id)

    return {"messages": history}


# -----------------------------------
# Get All Chat Sessions
# -----------------------------------
@router.get("/sessions")
async def list_sessions(session_ids: str):
    """Get all chat sessions for the user's known session IDs.

    session_ids is a comma-separated list of session UUIDs.
    """
    session_id_list = [s.strip() for s in session_ids.split(",") if s.strip()]
    sessions = get_all_sessions(session_ids=session_id_list)
    return {"sessions": sessions}


# -----------------------------------
# Create New Chat Session
# -----------------------------------
@router.post("/sessions")
async def new_session(source_session_id: str = None):
    """Create a new chat session.

    If source_session_id is provided, the new session will inherit
    context from that session (allowing new chats to use previously
    uploaded documents).
    """
    session_id = create_session(source_session_id=source_session_id)
    return {"session_id": session_id}


# -----------------------------------
# Delete Chat Session
# -----------------------------------
@router.delete("/sessions/{session_id}")
async def remove_session(session_id: str):
    delete_session(session_id)
    return {"message": "Session deleted"}


# -----------------------------------
# Rename Chat Session
# -----------------------------------
@router.put("/sessions/{session_id}")
async def update_session(session_id: str, body: dict):
    title = body.get("title", "")
    if not title:
        return {"error": "Title is required"}, 400
    success = rename_session(session_id, title)
    if not success:
        return {"error": "Session not found"}, 404
    return {"message": "Session renamed", "title": title}


# -----------------------------------
# Clear Chat History
# -----------------------------------
@router.delete("/clear-chat")
async def clear_chat(session_id: str):
    db: Session = SessionLocal()
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.commit()
    db.close()
    return {"message": "Chat cleared"}


# -----------------------------------
# Clear All Chats
# -----------------------------------
@router.delete("/clear-all-chats")
async def clear_all_chats():
    delete_all_sessions()
    return {"message": "All chats cleared"}
