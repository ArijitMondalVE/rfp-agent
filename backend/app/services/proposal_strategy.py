from groq import Groq
from app.core.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)


def generate_strategy(text: str):

    prompt = f"""
You are a senior proposal consultant.

Analyze this solicitation.

Generate:

1. Recommended response strategy
2. Key win themes
3. Risks
4. Critical compliance items
5. Bid / No Bid recommendation

Return JSON:

{{
 "response_strategy": [],
 "win_themes": [],
 "risks": [],
 "critical_items": [],
 "bid_recommendation": ""
}}

DOCUMENT:

{text[:12000]}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0,
        messages=[{"role":"user","content":prompt}]
    )

    return response.choices[0].message.content