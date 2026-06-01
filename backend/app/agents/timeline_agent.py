from openai import OpenAI
from app.core.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def extract_deadlines(chunk: str):

    prompt = f"""
    Extract all:
    - submission deadlines
    - project start dates
    - milestone dates
    - contract duration

    Return structured JSON.

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