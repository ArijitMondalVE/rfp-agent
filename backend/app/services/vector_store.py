import os
from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.core.config import HF_TOKEN
from app.services.chat_memory import get_source_session_id


# -----------------------------------
# EMBEDDINGS (lazy init to avoid crash on startup if HF_TOKEN missing)
# -----------------------------------
def get_embeddings():
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN environment variable is not set")
    return HuggingFaceEndpointEmbeddings(
        model="sentence-transformers/all-MiniLM-L6-v2",
        huggingfacehub_api_token=HF_TOKEN,
    )


# -----------------------------------
# CREATE VECTOR STORE
# -----------------------------------
def create_vector_store(session_id: str, chunks=None):
    """
    Create or replace the Chroma vector store
    for a specific session.
    """

    if chunks is None:
        raise ValueError("create_vector_store requires 'chunks'")

    collection_name = f"rfp_collection_{session_id}"
    persist_path = str(Path("chroma_db") / session_id)

    # Create persistent client
    client = chromadb.PersistentClient(path=persist_path)

    # Remove old collection if it exists
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass

    # Create vector store
    store = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=get_embeddings(),
    )

  # Add document chunks with metadata
    store.add_documents(chunks)

    return store


# -----------------------------------
# SEARCH VECTOR STORE
# -----------------------------------
def search_vector_store(session_id: str, query: str, k: int = 5):
    """
    Search the vector store for relevant chunks.
    Loads the session-specific store from disk.
    Falls back to source session's vector store if current session has none.
    """
    collection_name = f"rfp_collection_{session_id}"
    persist_path = str(Path("chroma_db") / session_id)

    if not Path(persist_path).exists():
        # Try source session's vector store
        source_session_id = get_source_session_id(session_id)
        if source_session_id:
            collection_name = f"rfp_collection_{source_session_id}"
            persist_path = str(Path("chroma_db") / source_session_id)
        else:
            return []

    try:
        client = chromadb.PersistentClient(path=persist_path)
        collection = client.get_collection(name=collection_name)

        store = Chroma(
            client=client,
            collection_name=collection_name,
            embedding_function=get_embeddings(),
        )

        return store.similarity_search(query, k=k)

    except Exception as e:
        print(f"Vector search error: {e}")
        return []