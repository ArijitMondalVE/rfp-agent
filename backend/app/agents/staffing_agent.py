import json

from app.services.llm_utils import generate_response


def extract_staffing(text: str):

    prompt = f"""
Extract staffing requirements.

Return JSON only.

[
  {{
    "requirement": "",
    "page": ""
  }}
]

Examples:

- Minimum experience
- Certifications
- Security clearances
- Personnel count

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