import json

from app.services.llm_utils import generate_response


def extract_deadlines(chunk: str):

    prompt = f"""
Extract all:

- submission deadlines
- project start dates
- milestone dates
- contract duration

Return JSON only.

Example:

{{
    "submission_deadline": "",
    "project_start_date": "",
    "milestones": [],
    "contract_duration": ""
}}

TEXT:

{chunk}
"""

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