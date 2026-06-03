import uuid
import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEndpointEmbeddings

embeddings = HuggingFaceEndpointEmbeddings(
    model="sentence-transformers/all-MiniLM-L6-v2",
    huggingfacehub_api_token=os.getenv("HF_TOKEN")
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
vector_store = None


# -----------------------------------
# CREATE VECTOR STORE
# -----------------------------------
def create_vector_store(chunks):

    global vector_store

    # Create unique collection
    collection_name = f"rfp_collection_{uuid.uuid4()}"

    # Create fresh in-memory vector store
    vector_store = Chroma.from_texts(
        texts=chunks, embedding=embeddings, collection_name=collection_name
    )

    return vector_store


# -----------------------------------
# SEARCH VECTOR STORE
# -----------------------------------
def search_vector_store(query: str, k: int = 5):

    global vector_store

    if vector_store is None:

        return []

    results = vector_store.similarity_search(query, k=k)

    return results
