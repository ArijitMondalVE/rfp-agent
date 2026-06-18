import json

from app.services.llm_utils import generate_response


def extract_forms(text: str):

    prompt = f"""
You are a Procurement Compliance Expert.

Extract ALL mandatory bidder forms.

Return JSON only.

[
  {{
    "form": "",
    "required": true,
    "page": "",
    "source_text": "",
    "confidence": "HIGH"
  }}
]

Include:

- Affidavits
- Certifications
- Attachments
- Exhibits
- Questionnaires
- Disclosure Forms
- Vendor Forms
- Bid Forms

Rules:

- Extract only explicitly required forms
- Include page number if available
- Include the exact sentence or clause where the requirement was found
- Confidence must be:
  HIGH
  MEDIUM
  LOW

Examples:

- W9
- Ownership Disclosure
- E-Verify
- Vendor Questionnaire
- Non-Collusion Affidavit
- Drug-Free Workplace Form

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
            f"Forms Agent Error: {e}"
        )

        return []