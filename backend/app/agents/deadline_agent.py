import json

from app.services.llm_utils import generate_response


def extract_deadlines(text: str):

    prompt = f"""
Extract ALL important procurement dates.

Return JSON only.

[
  {{
    "event": "",
    "date": "",
    "page": ""
  }}
]

Examples:

- Bid Due Date
- Questions Due
- Pre-Bid Conference
- Site Visit
- Contract Start

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