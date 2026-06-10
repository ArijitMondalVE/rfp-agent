import json

from backend.app.services.llm_utils import generate_response


def extract_rfp_details(chunk: str):

    prompt = f"""
You are an RFP analysis expert.

Extract:

- Scope of work
- Deadlines
- Staffing requirements
- Pricing details
- Compliance clauses

Return JSON only.

Example:

{{
  "scope_of_work": [],
  "deadlines": [],
  "staffing_requirements": [],
  "pricing_details": [],
  "compliance_clauses": []
}}

TEXT:

{chunk}
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

        print(f"RFP Detail Extractor Error: {e}")

        return {
            "scope_of_work": [],
            "deadlines": [],
            "staffing_requirements": [],
            "pricing_details": [],
            "compliance_clauses": []
        }