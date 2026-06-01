from sqlalchemy.orm import Session

from app.db.database import SessionLocal

from app.models.chat_message import ChatMessage

from app.models.conversation import Conversation

from datetime import datetime


# -----------------------------------
# Save Chat Message
# -----------------------------------
def save_chat_message(session_id: str, role: str, content: str):

    db: Session = SessionLocal()

    # Create session if it doesn't exist
    conversation = db.query(Conversation).filter(Conversation.session_id == session_id).first()
    if not conversation:
        conversation = Conversation(session_id=session_id, title="New Chat")
        db.add(conversation)
        db.flush()

    message = ChatMessage(session_id=session_id, role=role, content=content)

    db.add(message)

    # Update conversation's updated_at timestamp
    conversation.updated_at = datetime.utcnow()
    # Update title from first user message if still default
    if conversation.title == "New Chat" and role == "user":
        conversation.title = content[:50] + ("..." if len(content) > 50 else "")

    db.commit()

    db.close()


# -----------------------------------
# Get Conversation History
# -----------------------------------
def get_chat_history(session_id: str):

    db: Session = SessionLocal()

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.asc())
        .limit(20)
        .all()
    )

    db.close()

    return [{"role": msg.role, "content": msg.content} for msg in messages]


# -----------------------------------
# Create New Session
# -----------------------------------
def create_session() -> str:
    """Create a new conversation session and return its ID."""
    import uuid
    db: Session = SessionLocal()

    session_id = str(uuid.uuid4())
    conversation = Conversation(session_id=session_id, title="New Chat")
    db.add(conversation)
    db.commit()
    db.close()

    return session_id


# -----------------------------------
# Get All Sessions
# -----------------------------------
def get_all_sessions():
    """Get all conversation sessions ordered by most recent."""
    from sqlalchemy import text

    db: Session = SessionLocal()

    try:
        # Query conversations table using SQLAlchemy ORM
        rows = db.execute(
            text("SELECT id, session_id, role, content, title, created_at, updated_at FROM conversations ORDER BY id DESC")
        ).fetchall()

        seen = set()
        sessions = []
        for row in rows:
            # Row order: (id, session_id, role, content, title, created_at, updated_at)
            _id, session_id, role, content, title, created_at, updated_at = row
            if session_id in seen:
                continue
            seen.add(session_id)

            # Use title from DB if not default "New Chat" and available
            session_title = title if title and title != "New Chat" else "New Chat"

            # For preview, try to get last message from chat_messages table
            preview = "No messages"

            sessions.append({
                "session_id": session_id,
                "title": session_title,
                "preview": preview,
                "updated_at": str(updated_at) if updated_at else None,
            })

        db.close()
        return sessions

    except Exception:
        # Fallback: if query fails, return an empty list instead of 500.
        db.close()
        return []



# -----------------------------------
# Delete Session
# -----------------------------------
def delete_session(session_id: str):
    """Delete a conversation session and all its messages."""
    db: Session = SessionLocal()

    # Delete all messages for this session
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()

    # Delete the conversation
    db.query(Conversation).filter(Conversation.session_id == session_id).delete()

    db.commit()
    db.close()


# -----------------------------------
# Delete All Sessions
# -----------------------------------
def delete_all_sessions():
    """Delete all conversation sessions and messages."""
    db: Session = SessionLocal()

    # Delete all messages
    db.query(ChatMessage).delete()

    # Delete all conversations
    db.query(Conversation).delete()

    db.commit()
    db.close()


# -----------------------------------
# Rename Session
# -----------------------------------
def rename_session(session_id: str, title: str) -> bool:
    """Rename a conversation session title."""
    db: Session = SessionLocal()

    conversation = db.query(Conversation).filter(Conversation.session_id == session_id).first()
    if not conversation:
        db.close()
        return False

    conversation.title = title
    db.commit()
    db.close()
    return True
