from app.core.config import MODEL_OPENAI
from app.services.llm_provider import openai_client


def generate_response(
    messages,
    temperature=0,
    stream=False,
    response_format=None,
    provider: str = "openai",
):
    """Generate OpenAI LLM response.

    Args:
        messages: OpenAI-format messages
        temperature: Sampling temperature (default 0)
        stream: Enable streaming (default False)
        response_format: JSON schema for structured output
        provider: 'openai' only (kept for signature compatibility)

    Returns:
        OpenAI ChatCompletion response
    """
    # Always use OpenAI
    model = MODEL_OPENAI

    params = {
        "model": model,
        "messages": messages,
        "stream": stream,
    }
    if response_format:
        params["response_format"] = response_format
    if temperature:
        params["temperature"] = temperature

    return openai_client.chat.completions.create(**params)