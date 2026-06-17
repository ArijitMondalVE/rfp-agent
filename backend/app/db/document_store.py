import sqlite3
import json
import time
from pathlib import Path

DB_FILE = str((Path(__file__).resolve().parents[2] / "documents.db"))

DEFAULT_SQLITE_TIMEOUT_S = 5.0
DEFAULT_SQLITE_RETRIES = 3
DEFAULT_SQLITE_RETRY_BACKOFF_S = 0.25


def _connect():
    conn = sqlite3.connect(DB_FILE, timeout=DEFAULT_SQLITE_TIMEOUT_S)
    # Reduce likelihood of "database is locked" under concurrent readers/writers.
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "PRAGMA busy_timeout = {}".format(int(DEFAULT_SQLITE_TIMEOUT_S * 1000))
    )
    return conn


def _with_retry(fn, *, retries: int = DEFAULT_SQLITE_RETRIES):
    last_err = None
    for attempt in range(retries):
        try:
            return fn()
        except sqlite3.OperationalError as e:
            # SQLite returns this when another connection holds a lock.
            if "database is locked" not in str(e).lower():
                raise
            last_err = e
            if attempt < retries - 1:
                time.sleep(DEFAULT_SQLITE_RETRY_BACKOFF_S * (attempt + 1))
    raise last_err


# ==========================
# DATABASE INIT
# ==========================


def init_db():

    conn = _connect()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        session_id TEXT,
        filename TEXT,
        pdf_path TEXT,
        summary TEXT,      
        structured_data TEXT,
        compliance_matrix TEXT,
        classification TEXT,
        proposal_strategy TEXT,
        procurement_kb TEXT,
        executive_brief TEXT,
        opportunity_assessment TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Track in-progress uploads so the user can cancel before embeddings/doc persistence.
    conn.execute("""
    CREATE TABLE IF NOT EXISTS upload_jobs (
        id TEXT PRIMARY KEY,

        session_id TEXT NOT NULL,
        filename TEXT,
        pdf_path TEXT,

        status TEXT NOT NULL,
        cancelled_at TIMESTAMP,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

    # Migrate old table (add missing column if exists from old schema)
    try:
        conn = _connect()
        conn.execute("ALTER TABLE documents ADD COLUMN opportunity_assessment TEXT")
        conn.commit()
    except:
        pass
    finally:
        conn.close()


# ==========================
# UPLOAD JOBS (cancel support)
# ==========================


def create_upload_job(
    *, job_id: str, session_id: str, filename: str, pdf_path: str
) -> None:

    def _do_insert():
        conn = _connect()
        try:
            conn.execute(
                """
                INSERT INTO upload_jobs(id, session_id, filename, pdf_path, status, cancelled_at, updated_at)
                VALUES(?,?,?,?,?,?, CURRENT_TIMESTAMP)
                """,
                (job_id, session_id, filename, pdf_path, "running", None),
            )
            conn.commit()
        finally:
            conn.close()

    _with_retry(_do_insert)


def set_upload_job_cancelled(job_id: str) -> str | None:
    """Returns job status after cancel request (or None if job not found)."""

    def _do_update():
        conn = _connect()
        try:
            cur = conn.execute(
                """
                UPDATE upload_jobs
                SET status = ?, cancelled_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status IN ('running')
                """,
                ("cancelled", job_id),
            )
            conn.commit()
            return cur.rowcount
        finally:
            conn.close()

    _with_retry(_do_update)

    job = get_upload_job(job_id)
    return job.get("status") if job else None


def get_upload_job(job_id: str):

    def _do_get():
        conn = _connect()
        try:
            cur = conn.execute(
                """
                SELECT id, session_id, filename, pdf_path, status, cancelled_at, created_at
                FROM upload_jobs
                WHERE id = ?
                """,
                (job_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "session_id": row[1],
                "filename": row[2],
                "pdf_path": row[3],
                "status": row[4],
                "cancelled_at": row[5],
                "created_at": row[6],
            }
        finally:
            conn.close()

    return _with_retry(_do_get)


def set_upload_job_status(job_id: str, status: str) -> None:

    def _do_update():
        conn = _connect()
        try:
            conn.execute(
                """
                UPDATE upload_jobs
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, job_id),
            )
            conn.commit()
        finally:
            conn.close()

    _with_retry(_do_update)


# ==========================
# SAVE DOCUMENT
# ==========================


def save_document(
    session_id,
    filename,
    pdf_path,
    summary,
    structured_data,
    compliance_matrix,
    classification,
    proposal_strategy,
    executive_brief,
    opportunity_assessment,
    procurement_kb,
):

    def _do_insert():
        conn = _connect()
        try:
            cursor = conn.execute(
                """
                INSERT INTO documents(
                    session_id,
                    filename,
                    pdf_path,
                    summary,
                    structured_data,
                    compliance_matrix,
                    classification,
                    proposal_strategy,
                    executive_brief,
                    opportunity_assessment,
                    procurement_kb
                )
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)                
                    """,
                (
                    (
                        session_id,
                        filename,
                        pdf_path,
                        summary,
                        json.dumps(structured_data, default=str),
                        json.dumps(compliance_matrix, default=str),
                        json.dumps(classification, default=str),
                        json.dumps(proposal_strategy, default=str),
                        executive_brief,
                        json.dumps(opportunity_assessment, default=str),
                        json.dumps(procurement_kb, default=str),
                    )
                ),
            )
            document_id = cursor.lastrowid
            conn.commit()
            return document_id
        finally:
            conn.close()

    return _with_retry(_do_insert)


# ==========================
# GET ALL DOCUMENTS (legacy - returns all)
# ==========================


def get_save_documents():

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.execute("""
        SELECT
            id,
            session_id,
            filename,
            created_at
        FROM documents
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return [
        {"id": row[0], "session_id": row[1], "filename": row[2], "created_at": row[3]}
        for row in rows
    ]


# ==========================
# GET DOCUMENTS BY SESSION
# ==========================


def get_documents_by_session(session_id: str):

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.execute(
        """
        SELECT
            id,
            session_id,
            filename,
            created_at
        FROM documents
        WHERE session_id = ?
        ORDER BY created_at DESC
    """,
        (session_id,),
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        {"id": row[0], "session_id": row[1], "filename": row[2], "created_at": row[3]}
        for row in rows
    ]


# ==========================
# GET SINGLE DOCUMENT
# ==========================


def get_document(document_id):

    def _do_get():
        conn = _connect()
        try:
            cursor = conn.execute(
                """
                SELECT
                    id,
                    session_id,
                    filename,
                    pdf_path,
                    summary,
                    structured_data,
                    compliance_matrix,
                    classification,
                    proposal_strategy,
                    procurement_kb,
                    executive_brief,
                    opportunity_assessment,
                    created_at
                FROM documents
                WHERE id = ?
                """,
                (document_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return row
        finally:
            conn.close()

    row = _with_retry(_do_get)

    if not row:
        return None

    return {
        "id": row[0],
        "session_id": row[1],
        "filename": row[2],
        "pdf_path": row[3],
        "summary": row[4],
        "structured_data": json.loads(row[5]) if row[5] else {},
        "compliance_matrix": json.loads(row[6]) if row[6] else [],
        "classification": json.loads(row[7]) if row[7] else {},
        "proposal_strategy": json.loads(row[8]) if row[8] else {},
        "procurement_kb": json.loads(row[9]) if row[9] else {},
        "executive_brief": row[10],
        "opportunity_assessment": json.loads(row[11]) if row[11] else {},
        "created_at": row[12],
    }


# ==========================
# DELETE DOCUMENT
# ==========================


def delete_document(document_id):

    def _do_delete():
        conn = _connect()
        try:
            conn.execute(
                """
                DELETE FROM documents
                WHERE id = ?
                """,
                (document_id,),
            )
            conn.commit()
        finally:
            conn.close()

    _with_retry(_do_delete)


# ==========================
# DELETE DOCUMENTS BY SESSION
# ==========================


def delete_documents_by_session(session_id: str):

    def _do_delete():
        conn = _connect()
        try:
            conn.execute(
                "DELETE FROM documents WHERE session_id = ?",
                (session_id,),
            )
            conn.commit()
        finally:
            conn.close()

    _with_retry(_do_delete)
