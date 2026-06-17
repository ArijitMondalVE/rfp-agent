import json

from app.services.llm_utils import generate_response


def extract_disqualifiers(text: str):

    prompt = f"""
Find requirements that could
cause disqualification.

Look for:

- Mandatory
- Must
- Shall
- Non-responsive
- Ineligible
- Disqualified

Return JSON only.

[
  {{
    "requirement":"",
    "reason":"",
    "page":""
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