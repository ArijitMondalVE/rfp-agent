from groq import Groq
from app.core.config import GROQ_API_KEY
import json

client = Groq(api_key=GROQ_API_KEY)


def generate_strategy(text):

    prompt = f"""
Analyze this solicitation.

Return JSON only.

{{
 "bid_recommendation":"",
 "response_strategy":[],
 "win_themes":[],
 "risks":[],
 "critical_items":[]
}}

Only use information present in the document.

If unavailable return:

"Not specified in RFP"

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