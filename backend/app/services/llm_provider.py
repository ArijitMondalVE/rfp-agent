from groq import Groq
from openai import OpenAI

from app.core.config import (
    ACTIVE_PROVIDER,
    GROQ_API_KEY,
    OPENAI_API_KEY
)


def get_client():

    if ACTIVE_PROVIDER == "openai":

        return OpenAI(
            api_key=OPENAI_API_KEY
        )

    return Groq(
        api_key=GROQ_API_KEY,
        timeout=120
    )


client = get_client()