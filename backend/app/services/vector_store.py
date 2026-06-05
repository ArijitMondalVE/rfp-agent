import uuid
import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEndpointEmbeddings

embeddings = HuggingFaceEndpointEmbeddings(
    model="sentence-transformers/all-MiniLM-L6-v2",
    huggingfacehub_api_token=os.getenv("HF_TOKEN"),
)


# # -----------------------------------
# # EMBEDDING MODEL
# # -----------------------------------
# embeddings = HuggingFaceEmbeddings(

#     model_name=
#     "sentence-transformers/all-MiniLM-L6-v2"
# )

# -----------------------------------
# GLOBAL VECTOR STORE
# -----------------------------------
vector_store = {}


# -----------------------------------
# CREATE VECTOR STORE
# -----------------------------------
def create_vector_store(session_id: str = "global", chunks=None):
    """Create (or replace) the Chroma vector store for a session."""
    global vector_store

    if chunks is None:
        raise ValueError("create_vector_store requires 'chunks'")

    collection_name = f"rfp_collection_{session_id}"

    vector_store[session_id] = Chroma.from_texts(
        texts=chunks, embedding=embeddings, collection_name=collection_name
    )

    return vector_store[session_id]



# -----------------------------------
# SEARCH VECTOR STORE
# -----------------------------------
def search_vector_store(session_id: str, query: str, k: int = 5):

    global vector_store

    store = vector_store.get(session_id)


    if not store:
        return []

    return store.similarity_search(query, k=k)
