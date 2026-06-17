import json

from app.services.llm_utils import generate_response


def generate_executive_brief(
    structured_data,
    procurement_kb,
    compliance_matrix,
    classification,
    proposal_strategy,
    
):

    prompt = f"""
You are a Senior Proposal Director.

Create an Executive Bid Briefing for leadership.

The purpose is to allow a Proposal Manager,
Capture Manager, or Executive Team member
to understand the opportunity WITHOUT
reading the full RFP.

IMPORTANT:

- Focus on business value
- Focus on compliance risks
- Focus on deadlines
- Focus on resource requirements
- Focus on win strategy
- Focus on bid/no-bid decision support

DO NOT repeat information.

DO NOT generate empty sections.

If information is unavailable:
"Not specified in RFP"

OUTPUT FORMAT

Executive Overview

Opportunity Snapshot

Client / Agency

Solicitation Information

Key Dates

Scope of Work

Required Deliverables

Staffing Requirements

Mandatory Forms

Evaluation Criteria

Insurance Requirements

Bond Requirements

Licenses & Certifications

Subcontractor Requirements

Contract Terms

Compliance Risks

Potential Disqualifiers

Proposal Challenges

Win Strategy Recommendations

Bid Recommendation

Executive Takeaways

DATA:

STRUCTURED DATA:
{json.dumps(structured_data, default=str)}

PROCUREMENT KNOWLEDGE BASE:
{json.dumps(procurement_kb, default=str)}

COMPLIANCE MATRIX:
{json.dumps(compliance_matrix, default=str)}

CLASSIFICATION:
{json.dumps(classification, default=str)}

PROPOSAL STRATEGY:
{json.dumps(proposal_strategy, default=str)}
"""

    response = generate_response(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content