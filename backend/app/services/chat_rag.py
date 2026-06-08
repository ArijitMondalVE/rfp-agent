from groq import Groq

from fastapi.responses import StreamingResponse

from app.core.config import GROQ_API_KEY

from app.services.vector_store import search_vector_store

from app.services.chat_memory import save_chat_message, get_chat_history

from app.services.context_memory import get_context

# ===================================
# GROQ CLIENT
# ===================================

client = Groq(api_key=GROQ_API_KEY, timeout=120)


# ===================================
# SUMMARY QUERY DETECTION
# ===================================

SUMMARY_KEYWORDS = [
    "summary",
    "summarize",
    "overview",
    "what is this pdf about",
    "what is this document about",
    "explain this pdf",
    "explain this document",
]


def is_summary_query(question: str):

    question = question.lower()

    return any(keyword in question for keyword in SUMMARY_KEYWORDS)


# ===================================
# FORMAT INSTRUCTIONS
# ===================================


def get_format_instruction(summary_query: bool):

    if not summary_query:
        return ""

    return """

Generate a professional structured summary of the document.

REQUIRED STRUCTURE:

Executive Summary

Main Topic

• Main topic point 1
• Main topic point 2

Objectives

• Objective 1
• Objective 2

Important Points

• Point 1
• Point 2
• Point 3

Requirements / Deliverables

• Requirement 1
• Requirement 2

Risks / Compliance Points

• Risk 1
• Risk 2

Important Insights

• Insight 1
• Insight 2

IMPORTANT RULES:

- DO NOT use markdown headings (#, ##, ###)
- DO NOT use asterisks (*)
- Use the bullet character "•" only
- Keep each bullet on its own line
- Leave one blank line between sections
- Never put a section title and content on the same line
- Never generate large paragraphs
- Extract information only from the document
- If a section is unavailable, omit it
- Make the output look like a professional report
"""


# ===================================
# RETRIEVE DOCUMENT CONTEXT
# ===================================


def retrieve_context(session_id: str, question: str):

    summary_query = is_summary_query(question)

    #temporary print for debugging
    for doc in docs:
        print("DOC METADATA:", doc.metadata)

    # Better retrieval for summaries
    search_query = "full document summary" if summary_query else question

    docs = search_vector_store(session_id, search_query, k=5 if summary_query else 3)
    if not docs:
        return "", summary_query

    context_parts = []

    for doc in docs:

        page = doc.metadata.get("page", "Unknown")

        context_parts.append(f"""
        ========================
        SOURCE PAGE: {page}
        ========================

        {doc.page_content[:1000]}
        """)

    context = "\n\n".join(context_parts)

    return context, summary_query


# ===================================
# RETRIEVE CHAT HISTORY
# ===================================


def retrieve_history(session_id: str):

    history = get_chat_history(session_id)

    return "\n".join([f"{msg['role']}: {msg['content'][:250]}" for msg in history[-4:]])


# ===================================
# RETRIEVE MEMORY
# ===================================


def retrieve_memory(session_id: str):

    stored_context = get_context(session_id)

    return "\n\n".join([memory.content[:400] for memory in stored_context[:2]])


# ===================================
# BUILD PROMPT
# ===================================


def build_prompt(
    question: str,
    context: str,
    history_text: str,
    memory_context: str,
    summary_query: bool,
):

    format_instruction = get_format_instruction(summary_query)

    return f"""
You are an intelligent AI document assistant.

Use the provided document context as the PRIMARY source of truth.

You MUST ONLY use information explicitly present in the retrieved document context.

If the information is not found in the document, respond exactly:

"Not specified in the RFP"

Do not infer or guess:
- Dates
- Agencies
- Locations
- Budgets
- Deadlines
- Requirements
- Contract terms
- Evaluation criteria

Never fabricate information.

Do NOT fabricate unsupported facts.

Avoid overly defensive responses.

Answer naturally, clearly, and professionally.

IMPORTANT:

For every extracted fact:

1. State the fact.
2. Add "Source: Page X"

Example:

Agency:
City of Doral

Source: Page 2

Submission Deadline:
June 15, 2026

Source: Page 18

If a page number is unavailable:
Not specified in the RFP

Do not answer without a source page.

{format_instruction}

CHAT HISTORY:
{history_text}

MEMORY:
{memory_context}

DOCUMENT:
{context}

QUESTION:
{question}
"""


# ===================================
# NORMAL CHAT
# ===================================


def chat_with_rfp(session_id: str, question: str):

    # Save user message
    save_chat_message(session_id, "user", question)

    # Retrieve context
    context, summary_query = retrieve_context(session_id, question)

    # Empty context
    if not context.strip():
        # Provide a more actionable message when the vector store/session context is missing.
        answer = (
            "No relevant information was found in the uploaded document. "
            "This can happen if the document was not uploaded for this session or "
            "the server restarted and the in-memory vector index is missing. "
            "Please re-upload the document for this session and try again."
        )

        save_chat_message(session_id, "assistant", answer)

        return {"session_id": session_id, "question": question, "answer": answer}

    # Retrieve history
    history_text = retrieve_history(session_id)

    # Retrieve memory
    memory_context = retrieve_memory(session_id)

    # Build prompt
    prompt = build_prompt(
        question, context, history_text, memory_context, summary_query
    )

    # Generate response
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}],
    )

    answer = response.choices[0].message.content

    # Save assistant message
    save_chat_message(session_id, "assistant", answer)

    return {"session_id": session_id, "question": question, "answer": answer}


# ===================================
# STREAMING CHAT
# ===================================


async def stream_chat_with_rfp(session_id: str, question: str):

    # Save user message
    save_chat_message(session_id, "user", question)

    # Retrieve context
    context, summary_query = retrieve_context(session_id, question)

    # Empty context
    if not context.strip():

        async def empty_response():

            yield (
                "data: No relevant information was found in the uploaded document. "
                "This can happen if the document was not uploaded for this session or "
                "the server restarted and the in-memory vector index is missing. "
                "Please re-upload the document for this session and try again.\n\n"
                "was found in the uploaded document.\n\n"
            )

            yield "data: [DONE]\n\n"

        return StreamingResponse(empty_response(), media_type="text/event-stream")

    # Retrieve history
    history_text = retrieve_history(session_id)

    # Retrieve memory
    memory_context = retrieve_memory(session_id)

    # Build prompt
    prompt = build_prompt(
        question, context, history_text, memory_context, summary_query
    )

    # Start stream
    stream = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        stream=True,
        messages=[{"role": "user", "content": prompt}],
    )

    # Streaming generator
    async def generate():

        import asyncio

        full_response = ""

        try:

            for chunk in stream:

                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                if not delta:
                    continue

                content = delta.content

                if not content:
                    continue

                full_response += content

                yield f"data: {content}\n\n"

                await asyncio.sleep(0)

            yield "data: [DONE]\n\n"

            # Save AI response
            save_chat_message(session_id, "assistant", full_response)

        except Exception as e:

            yield f"data: Error: {str(e)}\n\n"

            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ===================================
# DOCUMENT SUMMARY GENERATOR
# ===================================


def generate_document_summary(text: str):

    shortened_text = text[:10000]

    prompt = f"""
Generate a professional document summary.

Structure:

Executive Summary

Main Topic

Objectives

Important Points

Requirements / Deliverables

Important Insights

Rules:

- Do NOT use markdown headings
- Do NOT use #, ##, ###
- Use the bullet character •
- Put each bullet on a separate line
- Leave one blank line between sections
- Keep the summary concise

DOCUMENT:
{shortened_text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content
