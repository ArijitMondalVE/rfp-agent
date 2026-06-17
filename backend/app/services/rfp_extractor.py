import json

from app.services.llm_utils import generate_response


def extract_rfp_metadata(text: str):
    """
    Extract structured procurement information from an RFP.
    Returns a Python dictionary.
    """

    shortened_text = text[:20000]

    prompt = f"""
You are a procurement and RFP analysis expert.

Analyze the document and extract structured information.

IMPORTANT RULES:

- Return VALID JSON ONLY
- Do NOT return markdown
- Do NOT return explanations
- Do NOT wrap JSON in ``` blocks
- Never invent information
- If a value is unavailable use:
  "Not specified"

Return this schema:

{{
  "solicitation_type": "",
  "solicitation_number": "",
  "agency": "",

  "submission_deadline": {{
    "value": "",
    "page": ""
  }},

  "contract_term": {{
    "value": "",
    "page": ""
  }},

  "submission_method": {{
    "value": "",
    "page": ""
  }},

  "licenses": [
    {{
      "requirement": "",
      "page": ""
    }}
  ],

  "insurance": [
    {{
      "requirement": "",
      "page": ""
    }}
  ],

  "mandatory_forms": [
    {{
      "form": "",
      "page": ""
    }}
  ],

  "evaluation_criteria": [
    {{
      "criterion": "",
      "page": ""
    }}
  ],

  "subcontractor_requirements": [
    {{
      "requirement": "",
      "page": ""
    }}
  ],

  "bond_requirements": [
    {{
      "requirement": "",
      "page": ""
    }}
  ]
}}

DOCUMENT:

{shortened_text}
"""

    try:

        response = generate_response(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content.strip()

        result = json.loads(content)
        # Ensure result is a dict before returning
        if not isinstance(result, dict):
            return {"error": "Invalid response format", "details": "Response was not a JSON object"}
        return result

    except Exception as e:

        print(f"RFP Extractor Error: {e}")

        return {
            "error": "Failed to parse JSON",
            "details": str(e)
        }