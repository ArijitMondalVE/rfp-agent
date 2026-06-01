from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import String

from app.db.database import Base


class ContextMemory(Base):

    __tablename__ = "context_memory"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    session_id = Column(String)

    context_type = Column(String)

    content = Column(Text)