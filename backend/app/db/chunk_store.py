import sqlite3
import json

DB_FILE = "documents.db"


DEFAULT_SQLITE_TIMEOUT_S = 5.0
DEFAULT_SQLITE_RETRIES = 3
DEFAULT_SQLITE_RETRY_BACKOFF_S = 0.25


def _connect():
    conn = sqlite3.connect(DB_FILE, timeout=DEFAULT_SQLITE_TIMEOUT_S)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout = {}".format(int(DEFAULT_SQLITE_TIMEOUT_S * 1000)))
    return conn


def _with_retry(fn, *, retries: int = DEFAULT_SQLITE_RETRIES):
    import time

    last_err = None
    for attempt in range(retries):
        try:
            return fn()
        except sqlite3.OperationalError as e:
            if "database is locked" not in str(e).lower():
                raise
            last_err = e
            if attempt < retries - 1:
                time.sleep(DEFAULT_SQLITE_RETRY_BACKOFF_S * (attempt + 1))
    raise last_err


def init_chunk_table():

    conn = _connect()


    conn.execute("""
    CREATE TABLE IF NOT EXISTS document_chunks (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        document_id INTEGER,

        page INTEGER,

        content TEXT,

        metadata TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_chunks(document_id, chunks):

    conn = sqlite3.connect(DB_FILE)

    for chunk in chunks:

        conn.execute(
            """
            INSERT INTO document_chunks(
                document_id,
                page,
                content,
                metadata
            )
            VALUES(?,?,?,?)
            """,
            (
                document_id,
                chunk.metadata.get("page", 0),
                chunk.page_content,
                json.dumps(chunk.metadata, default=str),
            ),
        )

    conn.commit()
    conn.close()


def get_chunks(document_id):

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.execute(
        """
        SELECT page, content, metadata
        FROM document_chunks
        WHERE document_id=?
        """,
        (document_id,),
    )

    rows = cursor.fetchall()

    conn.close()

    return rows


def delete_chunks(document_id):

    conn = sqlite3.connect(DB_FILE)

    conn.execute(
        """
        DELETE FROM document_chunks
        WHERE document_id=?
        """,
        (document_id,),
    )

    conn.commit()
    conn.close()