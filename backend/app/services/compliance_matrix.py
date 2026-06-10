import json
from groq import Groq

from app.core.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)


def generate_compliance_matrix(text: str):
    """
    Generate a compliance checklist from an RFP.

    Returns:
        list[dict]
    """

    shortened_text = text[:20000]

    prompt = f"""
You are a government procurement compliance analyst.

Analyze the RFP and identify ALL mandatory requirements.

Return VALID JSON ONLY.

DO NOT return markdown.
DO NOT return explanations.
DO NOT wrap JSON in ``` blocks.

For every requirement return:

[
  {{
    "requirement": "",
    "category": "",
    "status": "Required",
    "page": ""
  }}
]

Categories may include:

- Forms
- Insurance
- Licensing
- Bonds
- Subcontractors
- Certifications
- Submission
- Staffing
- Technical
- Legal
- Financial

Examples:

[
  {{
    "requirement": "W-9 Form",
    "category": "Forms",
    "status": "Required",
    "page": 18
  }},
  {{
    "requirement": "General Liability Insurance $1,000,000",
    "category": "Insurance",
    "status": "Required",
    "page": 13
  }}
]

Only include requirements explicitly stated in the document.

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
        data = json.loads(content)

        if isinstance(data, list):
            return data

        return []

    except Exception:

        return [
            {
                "requirement": "Failed to parse compliance matrix",
                "category": "System",
                "status": "Error",
                "page": ""
            }
        ]