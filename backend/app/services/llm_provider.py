from groq import Groq
from openai import OpenAI

from app.core.config import (
    ACTIVE_PROVIDER,
    MODEL_GROQ,
    MODEL_OPENAI,
    GROQ_API_KEY,
    OPENAI_API_KEY
)


def get_client(provider: str = None):
    """Get LLM client. Default is ACTIVE_PROVIDER, or pass 'groq'/'openai' explicitly."""
    provider = provider or ACTIVE_PROVIDER

    if provider == "openai":
        return OpenAI(api_key=OPENAI_API_KEY)

    return Groq(api_key=GROQ_API_KEY, timeout=120)


# Default clients
groq_client = Groq(api_key=GROQ_API_KEY, timeout=120)
openai_client = OpenAI(api_key=OPENAI_API_KEY)
client = get_client()


def get_model(provider: str = None):
    """Get model name for the provider."""
    provider = provider or ACTIVE_PROVIDER

    if provider == "openai":
        return MODEL_OPENAI

    return MODEL_GROQ


def chat_with_fallback(messages: list, preferred_provider: str = None) -> dict:
    """Try preferred provider first, fallback on 429 rate limit error.

    Args:
        messages: OpenAI-format messages array
        preferred_provider: 'groq' or 'openai'. Default uses ACTIVE_PROVIDER.

    Returns:
        OpenAI-format response dict
    """
    preferred = preferred_provider or ACTIVE_PROVIDER

    # Try preferred provider first
    try:
        provider_client = groq_client if preferred == "groq" else openai_client
        model = MODEL_GROQ if preferred == "groq" else MODEL_OPENAI

        response = provider_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
        )
        return response.model_dump()

    except Exception as e:
        error_msg = str(e).lower()

        # Only fallback on rate limit (429) errors
        if "429" in error_msg or "rate_limit" in error_msg or "rate limit" in error_msg:
            print(f"[LLM] {preferred} rate limited, falling back to OpenAI...")

            # Fallback to other provider
            fallback_client = openai_client if preferred == "groq" else groq_client
            fallback_model = MODEL_OPENAI if preferred == "groq" else MODEL_GROQ

            response = fallback_client.chat.completions.create(
                model=fallback_model,
                messages=messages,
                temperature=0.1,
            )
            return response.modeldump()

        # Re-raise non-429 errors
        raise


def chat_completion(messages: list, provider: str = None):
    """Standard chat completion using configured provider."""
    provider = provider or ACTIVE_PROVIDER

    if provider == "openai":
        return openai_client.chat.completions.create(
            model=MODEL_OPENAI,
            messages=messages,
            temperature=0.1,
        )

    return groq_client.chat.completions.create(
        model=MODEL_GROQ,
        messages=messages,
        temperature=0.1,
    )