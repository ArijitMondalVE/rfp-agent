from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

DATABASE_URL = "sqlite:///./rfp_agent.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
Base.metadata.create_all(bind=engine)


# -----------------------------------
# MIGRATION: Add source_session_id column
# -----------------------------------
def run_migrations():
    """Add source_session_id column to conversations table if it doesn't exist."""
    with engine.connect() as conn:
        try:
            conn.execute(text(
                "ALTER TABLE conversations ADD COLUMN source_session_id VARCHAR"
            ))
            conn.commit()
        except Exception:
            # Column likely already exists
            pass

run_migrations()