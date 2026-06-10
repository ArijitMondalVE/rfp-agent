from groq import Groq
from app.core.config import GROQ_API_KEY
import json

client = Groq(api_key=GROQ_API_KEY)


def classify_rfp(text):

    prompt = f"""
Classify this procurement document.

Possible values:

- RFP
- RFQ
- ITB
- ITN
- RFSQ
- Other

Return JSON only.

Example:

{{
 "solicitation_type":"RFP",
 "confidence":0.92,
 "reason":"Contains proposal instructions and evaluation criteria"
}}

DOCUMENT:

{text[:12000]}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    return json.loads(
        response.choices[0].message.content
    )