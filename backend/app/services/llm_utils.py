from app.core.config import MODEL_OPENAI
from app.services.llm_provider import openai_client


def generate_response(
    messages,
    temperature=None,
    stream=False,
    response_format=None,
    provider: str = "openai",
    model=None,
):
    """
    Generate OpenAI response.
    """

    model = model or MODEL_OPENAI

    params = {
        "model": model,
        "messages": messages,
        "stream": stream,
    }

    if response_format:
        params["response_format"] = response_format

    # Only send temperature if explicitly provided
    if temperature is not None:
        params["temperature"] = temperature

    return openai_client.chat.completions.create(
        timeout=180,
        **params
    )