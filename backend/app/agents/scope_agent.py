import json

from app.services.llm_utils import generate_response


def extract_scope(doc):
    """
    Extract scope items from a LangChain Document
    while preserving page citations.
    """

    page = doc.metadata.get(
        "page",
        "Unknown"
    )

    chunk = doc.page_content

    prompt = f"""
You are an RFP Scope Analysis Expert.

Analyze the text and extract ONLY:

- Deliverables
- Services Required
- Objectives
- Exclusions

Rules:

- Use ONLY information explicitly present in the text
- Do NOT invent information
- Do NOT summarize
- Return ONLY a JSON array
- Each item must be a short requirement statement

Example:

[
  "Provide cloud migration services",
  "Develop technical documentation",
  "Project management support"
]

TEXT:

{chunk}
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

        content = response.choices[0].message.content.strip()

        # Remove markdown fences if model adds them
        content = content.replace(
            "```json",
            ""
        )

        content = content.replace(
            "```",
            ""
        ).strip()

        items = json.loads(content)

        if not isinstance(items, list):
            return []

        return [
            {
                "value": item,
                "page": page
            }
            for item in items
        ]

    except Exception as e:

        print(
            f"Scope Agent Error (Page {page}): {e}"
        )

        return []