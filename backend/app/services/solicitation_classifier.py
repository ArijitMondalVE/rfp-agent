import json

from app.services.llm_utils import generate_response


def classify_solicitation(text: str):

    prompt = f"""
Classify this procurement document.

Possible values:

- RFP
- RFQ
- ITB
- IFB
- ITN
- RFI
- Unknown

Return JSON only:

{{
  "solicitation_type":"",
  "confidence":"",
  "reason":""
}}

DOCUMENT:

{text[:12000]}
"""

    try:

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

    except Exception as e:

        print(f"Solicitation Classifier Error: {e}")

        return {
            "solicitation_type": "Unknown",
            "confidence": 0,
            "reason": "Classification failed"
        }