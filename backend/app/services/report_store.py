"""Database-backed store for generated RFP reports.

Each report is stored in the DB with its session_id for proper user isolation.
"""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.report import Report


# -----------------------------------
# SAVE REPORT (per session)
# -----------------------------------
def save_report(session_id: str, report_data: Dict[str, Any]) -> None:
    """Save or update the report for a given session."""
    import json

    db: Session = SessionLocal()

    try:
        # Check if report already exists for this session
        existing = db.query(Report).filter(Report.session_id == session_id).first()

        if existing:
            existing.report_json = json.dumps(report_data)
        else:
            report = Report(session_id=session_id, report_json=json.dumps(report_data))
            db.add(report)

        db.commit()
    finally:
        db.close()


# -----------------------------------
# GET REPORT (per session)
# -----------------------------------
def get_report(session_id: str) -> Optional[Dict[str, Any]]:
    """Get the report for a given session, or None if not found."""
    import json

    db: Session = SessionLocal()

    try:
        report = db.query(Report).filter(Report.session_id == session_id).first()

        if not report:
            return None

        return json.loads(report.report_json)
    finally:
        db.close()


# -----------------------------------
# DELETE REPORT (per session)
# -----------------------------------
def delete_report(session_id: str) -> None:
    """Delete the report for a given session."""
    db: Session = SessionLocal()

    try:
        db.query(Report).filter(Report.session_id == session_id).delete()
        db.commit()
    finally:
        db.close()
