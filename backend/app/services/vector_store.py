import uuid
import os
from pathlib import Path
import chromadb
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEndpointEmbeddings

embeddings = HuggingFaceEndpointEmbeddings(
    model="sentence-transformers/all-MiniLM-L6-v2",
    huggingfacehub_api_token=os.getenv("HF_TOKEN"),
)

# -----------------------------------
# PERSISTENCE CONFIG
# -----------------------------------
PERSIST_DIR = Path("chroma_db")


# -----------------------------------
# CREATE VECTOR STORE
# -----------------------------------
def create_vector_store(session_id: str = "global", chunks=None):
    """Create (or replace) the Chroma vector store for a session with persistence."""
    if chunks is None:
        raise ValueError("create_vector_store requires 'chunks'")

    collection_name = f"rfp_collection_{session_id}"
    persist_path = str(PERSIST_DIR / session_id)

    # Use PersistentClient for proper persistence
    client = chromadb.PersistentClient(path=persist_path)

    # Get or create collection
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass
    collection = client.get_or_create_collection(name=collection_name)

    store = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embeddings,
    )

    # Add documents
    store.add_texts(texts=chunks)

    return store


# -----------------------------------
# SEARCH VECTOR STORE
# -----------------------------------
def search_vector_store(session_id: str, query: str, k: int = 5):
    """Search the vector store. Loads from persistent storage if not in memory."""
    collection_name = f"rfp_collection_{session_id}"
    persist_path = str(PERSIST_DIR / session_id)

    # Try to load from persistent storage
    if not Path(persist_path).exists():
        return []

    try:
        client = chromadb.PersistentClient(path=persist_path)
        collection = client.get_collection(name=collection_name)
        store = Chroma(
            client=client,
            collection_name=collection_name,
            embedding_function=embeddings,
        )
        return store.similarity_search(query, k=k)
    except Exception:
        return []
