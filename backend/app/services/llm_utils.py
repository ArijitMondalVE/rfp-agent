from app.core.config import (
    ACTIVE_PROVIDER,
    MODEL_GROQ,
    MODEL_OPENAI
)

from app.services.llm_provider import (
    groq_client,
    openai_client
)


def generate_response(
    messages,
    stream=False,
    response_format=None,
    model=None,
):
    if ACTIVE_PROVIDER == "groq":

        return groq_client.chat.completions.create(
            model=model or MODEL_GROQ,
            messages=messages,
            stream=stream,
        )

    params = {
        "model": model or MODEL_OPENAI,
        "messages": messages,
        "stream": stream,
    }

    if response_format:
        params["response_format"] = response_format

    return openai_client.chat.completions.create(
        timeout=180,
        **params
    )