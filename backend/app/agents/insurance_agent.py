import json

from app.services.llm_utils import generate_response


def extract_insurance(text: str):

    prompt = f"""
You are a Procurement Insurance Compliance Expert.

Extract ALL insurance requirements.

Return JSON only.

[
  {{
    "coverage": "",
    "limit": "",
    "page": "",
    "source_text": "",
    "confidence": "HIGH"
  }}
]

Include:

- General Liability
- Workers Compensation
- Professional Liability
- Cyber Insurance
- Auto Liability
- Umbrella Coverage
- Errors & Omissions

Rules:

- Extract exact coverage limits whenever available
- Include page number if available
- Include the exact sentence or clause where the requirement was found
- Confidence must be:
  HIGH
  MEDIUM
  LOW

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
            f"Insurance Agent Error: {e}"
        )

        return []