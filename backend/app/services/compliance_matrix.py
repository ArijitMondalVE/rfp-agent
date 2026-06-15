import json

from app.services.llm_utils import generate_response


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

Only include requirements explicitly stated in the document.

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
        )

        content = response.choices[0].message.content.strip()

        # Remove markdown if model adds it
        content = content.replace("```json", "")
        content = content.replace("```", "").strip()

        data = json.loads(content)

        if isinstance(data, list):
            return data

        # Support object format too
        if isinstance(data, dict):
            return data.get("items", [])

        return []

    except Exception as e:

        print(f"Compliance Matrix Error: {e}")

        return [
            {
                "requirement": "Failed to parse compliance matrix",
                "category": "System",
                "status": "Error",
                "page": ""
            }
        ]