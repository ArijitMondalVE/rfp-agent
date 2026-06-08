from fastapi import FastAPI
from app.api.routes.rfp import router as rfp_router
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.db.database import engine
from app.db.database import Base

from app.models.user import User
from app.models.conversation import Conversation
from app.models.report import Report

app = FastAPI(title="RFP Intelligence Agent")

# Migration: add session_id column to reports table if it doesn't exist
with engine.connect() as conn:
    try:
        # Add session_id column (nullable first for migration)
        conn.execute(text("ALTER TABLE reports ADD COLUMN session_id VARCHAR(100)"))
        conn.commit()
    except Exception:
        pass  # Column already exists

    try:
        # Backfill existing rows with placeholder
        conn.execute(text("UPDATE reports SET session_id = 'legacy' WHERE session_id IS NULL"))
        conn.commit()
    except Exception:
        pass  # No rows to backfill or other error

Base.metadata.create_all(bind=engine)


app.add_middleware(
    CORSMiddleware,
    # Allow deployed frontends + local dev
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:\\d+|http://127\\.0\\.0\\.1:\\d+",
    allow_origins=[
        "https://rfp-agent-b8c2q1dl1-arijit-s-projects3.vercel.app",
        "https://rfp-agent-j7kfj6sk5-arijit-s-projects3.vercel.app",
        "https://rfp-agent.vercel.app",
        "https://rfp-agent-delta.vercel.app",
        # Local dev (Angular CLI typically runs on 4200)
        "http://localhost:3000",
        "http://localhost:4200",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(rfp_router)


@app.get("/")
def home():
    return {"message": "RFP Agent Running"}
