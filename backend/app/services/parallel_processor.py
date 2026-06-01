from concurrent.futures import ThreadPoolExecutor

from app.agents.scope_agent import extract_scope
from app.agents.timeline_agent import extract_deadlines


def process_chunk(chunk):

    return {
        "scope": extract_scope(chunk),
        "deadlines": extract_deadlines(chunk)
    }


def process_chunks_parallel(chunks):

    results = []

    with ThreadPoolExecutor(max_workers=5) as executor:

        futures = [
            executor.submit(process_chunk, chunk)
            for chunk in chunks
        ]

        for future in futures:

            results.append(future.result())

    return results