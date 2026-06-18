import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

# Provider
ACTIVE_PROVIDER = os.getenv("ACTIVE_PROVIDER", "openai")

# Models
MODEL_GROQ = os.getenv(
    "MODEL_GROQ",
    "llama-3.3-70b-versatile"
)

MODEL_OPENAI = os.getenv(
    "MODEL_OPENAI",
    "gpt-4.1-mini"
)


def get_active_model():
    if ACTIVE_PROVIDER == "openai":
        
        return MODEL_OPENAI

    return MODEL_GROQ