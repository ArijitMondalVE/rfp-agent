from openai import OpenAI
from app.core.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

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

    TEXT:
    {chunk}
    """

    response = client.chat.completions.create(
        model="gpt-5.5",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content