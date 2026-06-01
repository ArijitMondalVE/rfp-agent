import json
import shutil

from pathlib import Path
from datetime import datetime

from fastapi import (
    APIRouter,
    UploadFile,
    File
)

from fastapi.responses import (
    FileResponse
)

from sqlalchemy.orm import Session

from app.db.database import (
    SessionLocal
)

from app.models.report import (
    Report
)

from app.models.chat_message import (
    ChatMessage
)

from app.services.pdf_parser import (
    extract_text_from_pdf
)

from app.services.ocr_service import (
    extract_text_with_ocr
)

from app.services.chunker import (
    chunk_document
)

from app.services.async_processor import (
    process_chunks_async
)

from app.services.merger import (
    merge_results
)

from app.services.aggregator import (
    aggregate_results
)

from app.services.confidence import (
    add_confidence_scores
)

from app.services.vector_store import (

    create_vector_store,

    search_vector_store

)

from app.services.chat_rag import (

    chat_with_rfp,

    stream_chat_with_rfp,

    generate_document_summary

)

from app.services.chat_memory import (
    get_chat_history,
    create_session,
    get_all_sessions,
    delete_session,
    delete_all_sessions,
    rename_session,
)


from app.services.export_service import (

    generate_docx_report,

    generate_pdf_report

)

from app.services.context_memory import (
    save_context
)

from app.services import report_store


# -----------------------------------
# Router
# -----------------------------------
router = APIRouter(

    prefix="/rfp",

    tags=["RFP"]

)

UPLOAD_DIR = "uploads"

Path(
    UPLOAD_DIR
).mkdir(exist_ok=True)


# -----------------------------------
# Upload + Process RFP
# -----------------------------------
@router.post("/upload")
async def upload_rfp(
    file: UploadFile = File(...)
):

    # -----------------------------------
    # Save uploaded file
    # -----------------------------------
    file_path = Path(
        UPLOAD_DIR
    ) / file.filename

    with open(
        file_path,
        "wb"
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    # -----------------------------------
    # Extract PDF text
    # -----------------------------------
    text = extract_text_from_pdf(
        str(file_path)
    )

    # -----------------------------------
    # OCR fallback
    # -----------------------------------
    if len(text.strip()) < 500:

        print(
            "Low text detected. Running OCR..."
        )

        text = extract_text_with_ocr(
            str(file_path)
        )

    # -----------------------------------
    # Generate executive summary
    # -----------------------------------
    document_summary = generate_document_summary(
        text
    )

    # -----------------------------------
    # Save context memory
    # -----------------------------------
    save_context(

        session_id="global",

        context_type="summary",

        content=document_summary
    )

    save_context(

        session_id="global",

        context_type="document_name",

        content=file.filename
    )

    save_context(

        session_id="global",

        context_type="upload_time",

        content=str(datetime.now())
    )

    # -----------------------------------
    # Chunk document
    # -----------------------------------
    chunks = chunk_document(
        text
    )

    # -----------------------------------
    # Store embeddings
    # -----------------------------------
    create_vector_store(
        chunks
    )

    # -----------------------------------
    # Run AI extraction
    # -----------------------------------
    results = await process_chunks_async(
        chunks[:5]
    )

    # -----------------------------------
    # Merge extracted results
    # -----------------------------------
    merged = merge_results(
        results
    )

    # -----------------------------------
    # Aggregate structured report
    # -----------------------------------
    aggregated = aggregate_results(
        merged
    )

    # -----------------------------------
    # Add summary
    # -----------------------------------
    aggregated["summary"] = [

        {
            "value": document_summary
        }

    ]

    # -----------------------------------
    # Add confidence scores
    # -----------------------------------
    aggregated["scope_of_work"] = (
        add_confidence_scores(
            aggregated.get(
                "scope_of_work",
                []
            )
        )
    )

    aggregated["deadlines"] = (
        add_confidence_scores(
            aggregated.get(
                "deadlines",
                []
            )
        )
    )

    aggregated["staffing_requirements"] = (
        add_confidence_scores(
            aggregated.get(
                "staffing_requirements",
                []
            )
        )
    )

    aggregated["compliance_items"] = (
        add_confidence_scores(
            aggregated.get(
                "compliance_items",
                []
            )
        )
    )

    # -----------------------------------
    # Save structured report memory
    # -----------------------------------
    save_context(

    session_id="global",

    context_type="important_points",

    content=f"""
    Scope:
    {aggregated.get('scope_of_work', [])}

    Deadlines:
    {aggregated.get('deadlines', [])}

    Compliance:
    {aggregated.get('compliance_items', [])}
    """
)

    # -----------------------------------
    # Store latest report in memory
    # -----------------------------------
    report_store.latest_report.clear()

    report_store.latest_report.update(
        aggregated
    )

    # -----------------------------------
    # Save report to database
    # -----------------------------------
    db: Session = SessionLocal()

    report = Report(

        report_json=json.dumps(
            aggregated
        )

    )

    db.add(report)

    db.commit()

    db.close()

    # -----------------------------------
    # API Response
    # -----------------------------------
    return {

        "filename": file.filename,

        "characters": len(text),

        "preview": text[:1000],

        "total_chunks": len(chunks),

        "processed_chunks": len(results),

        "report": aggregated

    }


# -----------------------------------
# Get Latest Report JSON
# -----------------------------------
@router.get("/report")
async def get_report():
    """Fetch the latest report JSON for preview."""
    if not report_store.latest_report:
        return {"error": "No report available. Upload an RFP first."}, 404

    return report_store.latest_report


# -----------------------------------
# Semantic Search API
# -----------------------------------
@router.get("/search")
async def search_rfp(
    query: str
):

    results = search_vector_store(
        query
    )

    return {

        "query": query,

        "results": [

            doc.page_content

            for doc in results
        ]
    }


# -----------------------------------
# Normal Chat API
# -----------------------------------
@router.get("/chat")
async def chat_rfp(

    session_id: str,

    question: str

):

    response = chat_with_rfp(

        session_id,

        question

    )

    return response


# -----------------------------------
# Streaming Chat API
# -----------------------------------
@router.get("/stream-chat")
async def stream_chat(
    session_id: str,
    question: str
):

    return await stream_chat_with_rfp(
        session_id,
        question
    )


# -----------------------------------
# Export DOCX
# -----------------------------------
@router.get("/export-docx")
async def export_docx():

    file_path = generate_docx_report(
        report_store.latest_report
    )

    return FileResponse(

        path=file_path,

        filename="rfp_report.docx",

        media_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    )


# -----------------------------------
# Export PDF
# -----------------------------------
@router.get("/export-pdf")
async def export_pdf():

    file_path = generate_pdf_report(
        report_store.latest_report
    )

    return FileResponse(

        path=file_path,

        filename="rfp_report.pdf",

        media_type="application/pdf"
    )


# -----------------------------------
# Clear Chat History
# -----------------------------------
@router.get("/chat-history")
async def chat_history(
    session_id: str
):
    # Return messages in the format expected by the frontend.
    return {
        "messages": get_chat_history(session_id)
    }


# -----------------------------------
# Get All Chat Sessions
# -----------------------------------
@router.get("/sessions")
async def list_sessions():
    """Get all conversation sessions."""
    sessions = get_all_sessions()
    return {"sessions": sessions}


# -----------------------------------
# Create New Chat Session
# -----------------------------------
@router.post("/sessions")
async def new_session():
    """Create a new conversation session."""
    session_id = create_session()
    return {"session_id": session_id}


# -----------------------------------
# Delete Chat Session
# -----------------------------------
@router.delete("/sessions/{session_id}")
async def remove_session(session_id: str):
    """Delete a conversation session and all its messages."""
    delete_session(session_id)
    return {"message": "Session deleted"}


# -----------------------------------
# Rename Chat Session
# -----------------------------------
@router.put("/sessions/{session_id}")
async def update_session(session_id: str, body: dict):
    """Rename a conversation session."""
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
async def clear_chat(
    session_id: str
):
    db: Session = SessionLocal()

    db.query(
        ChatMessage
    ).filter(

        ChatMessage.session_id
        == session_id

    ).delete()

    db.commit()

    db.close()

    return {
        "message": "Chat cleared"
    }


# -----------------------------------
# Clear All Chats
# -----------------------------------
@router.delete("/clear-all-chats")
async def clear_all_chats():
    """Delete all conversation sessions and messages."""
    delete_all_sessions()
    return {"message": "All chats cleared"}
