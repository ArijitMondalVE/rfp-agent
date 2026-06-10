from app.services.llm_utils import generate_response


def generate_executive_summary(text: str) -> str:
    """Generate an executive brief for the entire RFP document."""

    prompt = f"""
You are an expert technical writer.

Create an executive summary (brief) of the DOCUMENT CONTENT provided below.

IMPORTANT:
- Base the summary ONLY on the given text.
- Do NOT describe the RFP category generically.
- Summarize what this uploaded document specifically contains.
- If the text is insufficient, say so.

Output format:

1) ONE paragraph (~150-300 words)

2) FIVE bullet points

Focus on:
- document purpose
- key sections
- major deadlines (if present)
- scope/deliverables (if present)
- notable requirements or constraints

TEXT:

{text[:15000]}
"""

    try:

        response = generate_response(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:

        print(f"Executive Summary Error: {e}")

        return (
            "Executive summary could not be generated due to a temporary AI service issue. "
            "Please try again later."
        )