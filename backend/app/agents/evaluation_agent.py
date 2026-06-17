import json

from app.services.llm_utils import generate_response


def extract_evaluation(text: str):

    prompt = f"""
Extract evaluation criteria.

Return JSON only.

[
  {{
    "criteria": "",
    "weight": "",
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