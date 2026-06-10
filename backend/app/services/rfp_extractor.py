import json
from groq import Groq

from app.core.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)


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

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    content = response.choices[0].message.content.strip()

    try:
        return json.loads(content)

    except Exception:
        return {
            "error": "Failed to parse JSON",
            "raw_response": content
        }