from app.core.config import ACTIVE_PROVIDER, get_active_model
from app.services.llm_provider import client


def generate_response(messages, temperature=0, stream=False, response_format=None):

    params = {
        "model": get_active_model(),
        "messages": messages,
        "stream": stream
    }
    if response_format:
        params["response_format"] = response_format

    if ACTIVE_PROVIDER == "groq":
        params["temperature"] = temperature

    return client.chat.completions.create(**params)