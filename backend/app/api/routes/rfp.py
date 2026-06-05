import json
import shutil

from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, UploadFile, File
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from app.db.database import SessionLocal
from app.models.chat_message import ChatMessage

from app.services.pdf_parser import extract_text_from_pdf
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

from app.services.export_service import generate_docx_report, generate_pdf_report
from app.services.context_memory import save_context
from app.services import report_store

# -----------------------------------
# Router
# -----------------------------------
router = APIRouter(prefix="", tags=["RFP"])

UPLOAD_DIR = "uploads"
Path(UPLOAD_DIR).mkdir(exist_ok=True)


# -----------------------------------
# Upload + Process RFP
# -----------------------------------
@router.post("/upload")
async def upload_rfp(session_id: str, file: UploadFile = File(...)):
    # Save uploaded file
    file_path = Path(UPLOAD_DIR) / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract PDF text
    text = extract_text_from_pdf(str(file_path))

    # OCR fallback
    if len(text.strip()) < 500:
        print("Low text detected. Running OCR...")
        text = extract_text_with_ocr(str(file_path))

    # Generate executive summary
    document_summary = generate_document_summary(text)

    # Save context memory
    save_context(session_id=session_id, context_type="summary", content=document_summary)
    save_context(session_id=session_id, context_type="document_name", content=file.filename)
    save_context(session_id=session_id, context_type="upload_time", content=str(datetime.now()))

    # Chunk document
    chunks = chunk_document(text)
    print("SESSION:", session_id)
    print("CHUNKS CREATED:", len(chunks))

    # Store embeddings
    create_vector_store(session_id=session_id, chunks=chunks)
    print("VECTOR STORE CREATED")

    # Run AI extraction (limited)
    results = await process_chunks_async(chunks[:5])

    # Merge extracted results
    merged = merge_results(results)

    # Aggregate structured report
    aggregated = aggregate_results(merged)

    # Add summary
    aggregated["summary"] = [{"value": document_summary}]

    # Add confidence scores
    aggregated["scope_of_work"] = add_confidence_scores(aggregated.get("scope_of_work", []))
    aggregated["deadlines"] = add_confidence_scores(aggregated.get("deadlines", []))
    aggregated["staffing_requirements"] = add_confidence_scores(
        aggregated.get("staffing_requirements", [])
    )
    aggregated["compliance_items"] = add_confidence_scores(aggregated.get("compliance_items", []))

    # Save structured report memory
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

    # Store report in database (per session)
    report_store.save_report(session_id, aggregated)

    # API Response
    return {
        "filename": file.filename,
        "characters": len(text),
        "preview": text[:1000],
        "total_chunks": len(chunks),
        "processed_chunks": len(results),
        "report": aggregated,
    }


# -----------------------------------
# Get Latest Report JSON
# -----------------------------------
@router.get("/documents")
async def get_documents():
    # return recent documents list
    return {"documents": []}


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
    return {"query": query, "results": [doc.page_content for doc in results]}


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

