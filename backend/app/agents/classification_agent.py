import json

from app.services.llm_utils import generate_response


def classify_rfp(text):

    prompt = f"""
Classify this procurement document.

Possible values:

- RFP
- RFQ
- ITB
- ITN
- RFSQ
- Other

Return JSON only.

Example:

{{
 "solicitation_type":"RFP",
 "confidence":0.92,
 "reason":"Contains proposal instructions and evaluation criteria"
}}

DOCUMENT:

{text[:12000]}
"""

    response = generate_response(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(
        response.choices[0].message.content
    )