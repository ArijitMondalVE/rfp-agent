import os
from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEndpointEmbeddings


# -----------------------------------
# EMBEDDINGS
# -----------------------------------
embeddings = HuggingFaceEndpointEmbeddings(
    model="sentence-transformers/all-MiniLM-L6-v2",
    huggingfacehub_api_token=os.getenv("HF_TOKEN"),
)


# -----------------------------------
# PERSISTENCE CONFIG
# -----------------------------------
PERSIST_DIR = Path("chroma_db")
PERSIST_DIR.mkdir(exist_ok=True)


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
    persist_path = str(PERSIST_DIR / session_id)

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
        embedding_function=embeddings,
    )

    # Add document chunks
    store.add_texts(texts=chunks)

    return store


# -----------------------------------
# SEARCH VECTOR STORE
# -----------------------------------
def search_vector_store(session_id: str, query: str, k: int = 5):
    """
    Search the vector store for relevant chunks.
    Loads the session-specific store from disk.
    """
    
    print("SEARCH SESSION:", session_id)

    collection_name = f"rfp_collection_{session_id}"
    persist_path = str(PERSIST_DIR / session_id)

    print("PATH:", persist_path)

    if not Path(persist_path).exists():
        return []

    try:
        client = chromadb.PersistentClient(path=persist_path)

        store = Chroma(
            client=client,
            collection_name=collection_name,
            embedding_function=embeddings,
        )

        results = store.similarity_search(query, k=k)

        print("RESULT COUNT:", len(results))

        return results

    except Exception as e:
        print(f"Vector search error: {e}")
        return []