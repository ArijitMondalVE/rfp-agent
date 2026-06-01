from groq import Groq

from app.core.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)


def generate_executive_summary(text: str) -> str:
    """Generate an executive brief for the entire RFP document."""
    prompt = f"""
You are an expert technical writer.

Create an executive summary (brief) of the DOCUMENT CONTENT provided below.

IMPORTANT:
- Base the summary ONLY on the given text.
- Do NOT describe the RFP “category” generically; summarize what this uploaded document specifically contains.
- If the text is insufficient, say so.

Output format:
1) ONE paragraph (~150-300 words)
2) FIVE bullet points

Focus on: document purpose, key sections, major deadlines (if present), scope/deliverables (if present), and any notable requirements or constraints.

TEXT:
{text}
"""

    # Try a small fallback-first chain to reduce rate-limit risk.
    # (Models/availability may vary by account; failures are handled.)
    model_chain = [
        "llama-3.2-1b-preview",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ]

    last_err = None

    for model in model_chain:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            last_err = e
            # If rate-limited, back off briefly and retry with next model.
            # (Groq exposes RateLimitError; we keep it generic to avoid import issues.)

    # If all models failed, return a safe placeholder instead of breaking upload.
    return (
        "Executive summary could not be generated due to temporary AI rate limits. "
        "Please try again later."
    )




