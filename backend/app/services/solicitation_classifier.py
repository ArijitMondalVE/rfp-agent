from groq import Groq
from app.core.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)


def classify_solicitation(text: str):

    prompt = f"""
Classify this procurement document.

Possible values:

- RFP
- RFQ
- ITB
- IFB
- ITN
- RFI
- Unknown

Return JSON only:

{{
  "solicitation_type":"",
  "confidence":"",
  "reason":""
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