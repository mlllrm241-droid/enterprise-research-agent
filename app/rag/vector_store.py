import os

from langchain_chroma import Chroma

from app.rag.embeddings import (
    get_embedding_model,
)


def get_knowledge_vector_store():
    """
    获取企业知识库 Vector Store。
    """

    persist_directory = os.getenv(
        "RAG_PERSIST_DIR",
        "data/chroma",
    )

    collection_name = os.getenv(
        "RAG_COLLECTION_NAME",
        "enterprise_knowledge",
    )

    return Chroma(
        collection_name=collection_name,

        embedding_function=(
            get_embedding_model()
        ),

        persist_directory=(
            persist_directory
        ),
    )