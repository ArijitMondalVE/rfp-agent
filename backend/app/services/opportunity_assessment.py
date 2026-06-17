import json

from app.services.llm_utils import generate_response


def assess_opportunity(
    procurement_kb,
    compliance_matrix,
    classification,
    proposal_strategy,
):
    prompt = f"""
You are a Bid/No-Bid opportunity analyst.

Analyze this RFP opportunity and provide an
opportunity assessment score and recommendation.

Return VALID JSON ONLY in this format:
{{
    "opportunity_score": 0-100,
    "risk_score": 0-100,
    "proposal_complexity": "Low" | "Medium" | "High",
    "bid_recommendation": "Bid" | "No Bid" | "Conditional Bid",
    "confidence": "Low" | "Medium" | "High",
    "reasons": ["reason 1", "reason 2", ...]
}}

Consider:
- Competition level
- Client relationship
- Resource availability
- Win probability
- Compliance burden
- Financial risk

DATA:

PROCUREMENT KNOWLEDGE BASE:
{json.dumps(procurement_kb, default=str)}

COMPLIANCE MATRIX:
{json.dumps(compliance_matrix, default=str)}

CLASSIFICATION:
{json.dumps(classification, default=str)}

PROPOSAL STRATEGY:
{json.dumps(proposal_strategy, default=str)}
"""

    response = generate_response(messages=[{"role": "user", "content": prompt}])

    try:
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Opportunity Assessment Error: {e}")
        return {
            "opportunity_score": None,
            "risk_score": None,
            "proposal_complexity": "Unknown",
            "bid_recommendation": "Unknown",
            "confidence": "Low",
            "reasons": [],
        }