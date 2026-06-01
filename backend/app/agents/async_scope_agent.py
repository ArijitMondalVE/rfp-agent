import json
import re

from groq import Groq

from app.core.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)


def clean_json_string(raw: str) -> str:
    """Remove markdown code blocks and explanatory text from LLM output."""
    # Remove ```json and ``` markers
    raw = re.sub(r"```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```\s*$", "", raw)

    # Remove any text before first { or [
    first_bracket = min(
        raw.find("{") if "{" in raw else len(raw),
        raw.find("[") if "[" in raw else len(raw)
    )
    if first_bracket > 0:
        raw = raw[first_bracket:]

    return raw.strip()


def extract_structured_field(text: str, field: str) -> list:
    """Extract clean bullet points from raw text, avoiding JSON blocks."""
    # Skip if it's a JSON block
    if text.strip().startswith(("{", "[")):
        return []

    lines = text.split("\n")
    items = []

    for line in lines:
        line = line.strip()
        # Match bullet points: -, *, •, or numbered items
        match = re.match(r"^[-*•]\s+(.+)", line)
        if match:
            items.append(match.group(1).strip())
            continue

        match = re.match(r"^\d+[.)]\s+(.+)", line)
        if match:
            items.append(match.group(1).strip())

    return items


async def async_extract_scope(chunk: str):

    prompt = f"""You are an RFP scope analysis expert. Extract the following from the document:
- scope of work (main tasks and services)
- deliverables (tangible outputs)
- objectives (goals and outcomes)

Format your response EXACTLY as a clean JSON object with this structure:
{{
  "scope_of_work": ["item 1", "item 2"],
  "deliverables": ["item 1", "item 2"],
  "objectives": ["item 1", "item 2"]
}}

Rules:
- Use plain text only, no markdown, no code blocks, no backticks
- Each array item should be a concise phrase (under 15 words)
- Do NOT include any explanatory text before or after the JSON
- If a field has no information, use an empty array: []

DOCUMENT TEXT:
{chunk}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1
    )

    raw_content = response.choices[0].message.content

    # Parse JSON response
    cleaned = clean_json_string(raw_content)

    try:
        parsed = json.loads(cleaned)
        scope_items = parsed.get("scope_of_work", [])
        deliverables = parsed.get("deliverables", [])
        objectives = parsed.get("objectives", [])
    except json.JSONDecodeError:
        # Fallback: extract bullet points from raw text
        scope_items = extract_structured_field(raw_content, "scope")
        deliverables = []
        objectives = []

    return {
        "scope": scope_items,
        "deliverables": deliverables,
        "objectives": objectives
    }