from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text

from app.db.database import Base


class Report(Base):

    __tablename__ = "reports"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    report_json = Column(Text)