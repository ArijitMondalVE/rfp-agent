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

app.include_router(rfp_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "RFP Agent Running"}

