from sqlalchemy.orm import Session

from app.db.database import SessionLocal

from app.models.conversation import Conversation


def save_message(session_id, role, content):

    db: Session = SessionLocal()

    message = Conversation(
        session_id=session_id,
        role=role,
        content=content
    )

    db.add(message)

    db.commit()

    db.close()


def get_conversation(session_id):

    db: Session = SessionLocal()

    messages = db.query(Conversation).filter(
        Conversation.session_id == session_id
    ).all()

    db.close()

    return [
        {
            "role": msg.role,
            "content": msg.content
        }
        for msg in messages
    ]