from fastapi import FastAPI
from app.api.routes.rfp import router as rfp_router
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine
from app.db.database import Base

from app.models.user import User
from app.models.conversation import Conversation
from app.models.report import Report

app = FastAPI(title="RFP Intelligence Agent")

Base.metadata.create_all(bind=engine)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://rfp-agent-b8c2q1dl1-arijit-s-projects3.vercel.app",
        "https://rfp-agent-j7kfj6sk5-arijit-s-projects3.vercel.app",
        "https://rfp-agent.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(rfp_router)


@app.get("/")
def home():
    return {"message": "RFP Agent Running"}
