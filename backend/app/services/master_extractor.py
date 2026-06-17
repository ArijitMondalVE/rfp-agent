import json

from app.services.llm_utils import generate_response


def extract_all_at_once(text: str) -> dict:
    """
    Single LLM call to extract ALL procurement data.
    This is ~7x faster than 7 separate calls.
    """

    prompt = f"""
You are a procurement data extractor. Extract ALL information from this RFP in a SINGLE call.

Return VALID JSON ONLY with this exact structure:

{{
    "deadlines": [
        {{"event": "", "date": "", "page": ""}}
    ],
    "forms": [
        {{"form": "", "description": "", "page": ""}}
    ],
    "insurance": [
        {{"type": "", "amount": "", "page": ""}}
    ],
    "staffing": [
        {{"role": "", "quantity": "", "requirements": "", "page": ""}}
    ],
    "evaluation": [
        {{"criterion": "", "weight": "", "page": ""}}
    ],
    "contract": [
        {{"term": "", "renewal": "", "page": ""}}
    ],
    "disqualifiers": [
        {{"reason": "", "page": ""}}
    ]
}}

Rules:
- Use "Not specified" for missing info
- Include page numbers when found
- Be thorough but accurate

TEXT (first 12K chars):

{text[:12000]}
"""

    try:
        response = generate_response(
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content.strip()
        result = json.loads(content)

        if isinstance(result, dict):
            return result
        return {"error": "Invalid response"}

    except Exception as e:
        print(f"Combined extraction error: {e}")
        return {
            "deadlines": [],
            "forms": [],
            "insurance": [],
            "staffing": [],
            "evaluation": [],
            "contract": [],
            "disqualifiers": []
        }


def build_procurement_kb(text, structured_data=None, classification=None, strategy=None):
    """
    Build procurement knowledge base using efficient SINGLE call extractor.
    This replaces 7 slow sequential agent calls with 1 fast call.
    """

    return extract_all_at_once(text)