import json

from app.services.llm_utils import generate_response


def generate_strategy(text: str):

    prompt = f"""
You are a senior proposal consultant.

Analyze this solicitation.

Generate:

1. Recommended response strategy
2. Key win themes
3. Risks
4. Critical compliance items
5. Bid / No Bid recommendation

Return JSON ONLY:

{{
  "response_strategy": [],
  "win_themes": [],
  "risks": [],
  "critical_items": [],
  "bid_recommendation": ""
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

        print(f"Strategy Agent Error: {e}")

        return {
            "response_strategy": [],
            "win_themes": [],
            "risks": [],
            "critical_items": [],
            "bid_recommendation": "Unable to determine"
        }