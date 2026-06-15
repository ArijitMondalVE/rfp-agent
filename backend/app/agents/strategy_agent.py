import json

from app.services.llm_utils import generate_response


def generate_strategy(text):

    prompt = f"""
Analyze this solicitation.

Return JSON only.

{{
 "bid_recommendation":"",
 "response_strategy":[],
 "win_themes":[],
 "risks":[],
 "critical_items":[]
}}

Only use information present in the document.

If unavailable return:

"Not specified in RFP"

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
        response_format={"type": "json_object"},
    )

    return json.loads(
        response.choices[0].message.content
    )