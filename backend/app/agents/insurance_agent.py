import json

from app.services.llm_utils import generate_response


def extract_insurance(text: str):

    prompt = f"""
Extract all insurance requirements.

Return JSON only.

[
  {{
    "coverage": "",
    "limit": "",
    "page": ""
  }}
]

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