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
    conn.execute("PRAGMA busy_timeout = {}".format(int(DEFAULT_SQLITE_TIMEOUT_S * 1000)))
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

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


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
                    proposal_strategy
                )
                VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    session_id,
                    filename,
                    pdf_path,
                    summary,
                    json.dumps(structured_data, default=str),
                    json.dumps(compliance_matrix, default=str),
                    json.dumps(classification, default=str),
                    json.dumps(proposal_strategy, default=str),
                ),
            )
            document_id = cursor.lastrowid
            conn.commit()
            return document_id
        finally:
            conn.close()

    return _with_retry(_do_insert)



# ==========================
# GET ALL DOCUMENTS
# ==========================


def get_save_documents():

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.execute("""
        SELECT
            id,
            filename,
            created_at
        FROM documents
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return [{"id": row[0], "filename": row[1], "created_at": row[2]} for row in rows]


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
        "created_at": row[9],
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

