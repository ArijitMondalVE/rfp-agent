import asyncio

from app.agents.async_scope_agent import async_extract_scope


async def process_chunks_async(chunks):

    tasks = [
        async_extract_scope(chunk)
        for chunk in chunks
    ]

    results = await asyncio.gather(*tasks)

    return results