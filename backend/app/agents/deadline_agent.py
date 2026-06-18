import json

from app.services.llm_utils import generate_response


def extract_deadlines(text: str):

    prompt = f"""
You are a Procurement Schedule Extraction Expert.

Extract ALL procurement-related dates and milestones.

Return JSON only.

[
  {{
    "event": "",
    "date": "",
    "page": "",
    "source_text": "",
    "confidence": "HIGH"
  }}
]

Rules:

- Extract exact dates whenever possible
- Include page number if available
- Include the sentence or clause where the date was found
- Do NOT invent dates
- Return only valid JSON
- Confidence must be:
  HIGH
  MEDIUM
  LOW

Examples:

- Bid Due Date
- Questions Due Date
- Pre-Bid Conference
- Site Visit
- Contract Start Date
- Proposal Submission Deadline
- Award Date

TEXT:

{text}
"""

    response = generate_response(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    try:

        content = response.choices[0].message.content

        content = content.replace(
            "```json",
            ""
        )

        content = content.replace(
            "```",
            ""
        ).strip()

        data = json.loads(content)

        if not isinstance(data, list):
            return []

        return data

    except Exception as e:

        print(
            f"Deadline Agent Error: {e}"
        )

        return []