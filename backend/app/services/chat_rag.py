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


def retrieve_context(question: str):

    summary_query = is_summary_query(question)

    # Better retrieval for summaries
    search_query = "full document summary" if summary_query else question

    docs = search_vector_store(search_query, k=5 if summary_query else 3)

    context = "\n\n".join([doc.page_content[:500] for doc in docs])

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


def retrieve_memory():

    stored_context = get_context("global")

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

You may infer reasonable conclusions from the context when appropriate.

Do NOT fabricate unsupported facts.

Avoid overly defensive responses.

Answer naturally, clearly, and professionally.

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
    context, summary_query = retrieve_context(question)

    # Empty context
    if not context.strip():

        answer = "No relevant information " "was found in the uploaded document."

        save_chat_message(session_id, "assistant", answer)

        return {"session_id": session_id, "question": question, "answer": answer}

    # Retrieve history
    history_text = retrieve_history(session_id)

    # Retrieve memory
    memory_context = retrieve_memory()

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
    context, summary_query = retrieve_context(question)

    # Empty context
    if not context.strip():

        async def empty_response():

            yield (
                "data: No relevant information "
                "was found in the uploaded document.\n\n"
            )

            yield "data: [DONE]\n\n"

        return StreamingResponse(empty_response(), media_type="text/event-stream")

    # Retrieve history
    history_text = retrieve_history(session_id)

    # Retrieve memory
    memory_context = retrieve_memory()

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
Summarize this document professionally.

Include:
- Main topic
- Objectives
- Important points
- Key requirements
- Deliverables if available

Use markdown formatting.
Use bullet points.
Keep response concise and readable.

DOCUMENT:
{shortened_text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content
