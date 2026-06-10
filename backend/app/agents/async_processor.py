import asyncio

from app.agents.async_scope_agent import async_extract_scope
from app.agents.compliance import extract_compliance
from app.agents.timeline_agent import extract_timeline
from app.agents.classification_agent import classify_rfp
from app.agents.strategy_agent import generate_strategy


async def process_chunks_async(chunks):

    full_text = "\n\n".join(chunks)

    scope_tasks = [
        async_extract_scope(chunk)
        for chunk in chunks
    ]

    scope_results = await asyncio.gather(*scope_tasks)

    compliance = extract_compliance(full_text)

    timeline = extract_timeline(full_text)

    classification = classify_rfp(full_text)

    strategy = generate_strategy(full_text)

    return {
        "scope": scope_results,
        "compliance": compliance,
        "timeline": timeline,
        "classification": classification,
        "proposal_strategy": strategy
    }