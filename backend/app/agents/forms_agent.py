import json

from app.services.llm_utils import generate_response


def extract_forms(text: str):

    prompt = f"""
Extract ALL mandatory forms.

Return JSON only.

[
  {{
    "form": "",
    "required": true,
    "page": ""
  }}
]

Examples:

- W9
- Ownership Disclosure
- E-Verify
- Vendor Questionnaire

TEXT:

{text[:15000]}
"""

    response = generate_response(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    try:
        return json.loads(
            response.choices[0].message.content
        )
    except:
        return []