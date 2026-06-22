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
You are a Senior Capture Manager, Proposal Director, and Procurement Consultant.

Your task is to create an Executive Opportunity Briefing.

The audience is:

- CEO
- VP
- Capture Manager
- Proposal Manager
- Operations Director

The briefing should allow leadership to understand the opportunity WITHOUT reading the RFP.

========================
CRITICAL RULES
========================

1. Do NOT repeat information across sections.

2. If a fact is already mentioned,
   do not restate it elsewhere.

3. Do NOT generate empty sections.

4. Do NOT repeatedly write:
   "Not specified in the RFP"

Instead:

- Omit the item entirely
- Or write:
  "No explicit requirement identified"

5. Focus only on information important
   for bid decisions.

6. Prioritize:

- Deadlines
- Compliance requirements
- Staffing requirements
- Contract obligations
- Evaluation criteria
- Risks
- Win strategy

7. Consolidate related findings into
   a single insight whenever possible.

8. If a requirement appears under:

- General Conditions
- Special Conditions
- Forms
- Exhibits
- Attachments
- Scope of Work
- Contract Terms

Treat it as a valid requirement.

9. Highlight all potential disqualifiers.

10. Identify missing information that
    should be clarified with the agency.

11. Avoid generic statements.

12. Be specific and actionable.

13. Think like a Proposal Director
    preparing a bid/no-bid briefing.

========================
OUTPUT FORMAT
========================

# Executive Overview

Provide 5-10 concise bullets summarizing:

- Opportunity
- Client objectives
- Major requirements
- Key risks
- Important deadlines

# Opportunity Snapshot

Include:

- Agency
- Solicitation Number
- Solicitation Type
- Submission Deadline
- Contract Term

# Critical Deadlines

List all procurement milestones.

# Scope & Operational Requirements

Summarize:

- Services required
- Deliverables
- Staffing expectations
- Coverage requirements
- Operational requirements

# Compliance & Submission Requirements

Summarize:

- Mandatory forms
- Certifications
- Insurance requirements
- Bonds
- Licensing requirements
- Submission requirements

# Risk Assessment

Identify:

- Compliance risks
- Operational risks
- Proposal risks
- Potential disqualifiers

Assign:

Risk Level:
LOW / MEDIUM / HIGH

# Executive Action Items

List the 5-10 most important actions
the proposal team must complete.

Examples:

- Register on procurement portal
- Prepare mandatory forms
- Gather insurance certificates
- Obtain bonding documentation
- Validate staffing plan

# Win Strategy Recommendations

Provide practical recommendations
for improving competitiveness.

# Bid Recommendation

Return EXACTLY one:

GO

CONDITIONAL GO

NO GO

Then explain why.

# Executive Takeaways

Provide the 5 most important things
leadership should remember.

========================
DATA
========================

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
        ],
        model="gpt-4o",
    )

    return response.choices[0].message.content