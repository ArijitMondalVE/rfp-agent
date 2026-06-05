from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import String

from app.db.database import Base


class Report(Base):

    __tablename__ = "reports"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # session_id is nullable during migration, then backfilled
    # SQLAlchemy model reflects current state after migration
    session_id = Column(String(100), nullable=True, index=True)

    report_json = Column(Text)