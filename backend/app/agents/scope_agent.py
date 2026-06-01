from openai import OpenAI
from app.core.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def extract_scope(chunk: str):

    prompt = f"""
    You are an RFP scope analysis expert.

    Extract:
    - deliverables
    - services required
    - objectives
    - exclusions

    Return bullet points.

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