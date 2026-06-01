from sqlalchemy.orm import Session

from app.db.database import SessionLocal

from app.models.context_memory import (
    ContextMemory
)


# -----------------------------------
# Save Context
# -----------------------------------
def save_context(

    session_id: str,

    context_type: str,

    content: str

):

    db: Session = SessionLocal()

    memory = ContextMemory(

        session_id=session_id,

        context_type=context_type,

        content=content
    )

    db.add(memory)

    db.commit()

    db.close()


# -----------------------------------
# Retrieve Context
# -----------------------------------
def get_context(

    session_id: str
):

    db: Session = SessionLocal()

    memories = db.query(
        ContextMemory
    ).filter(

        ContextMemory.session_id
        == session_id

    ).limit(5).all()

    db.close()

    return memories