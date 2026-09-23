import os

from langchain_community.embeddings import DashScopeEmbeddings


def get_embedding_model():
    # =========================================
    # 1. 获取 Embedding 模型名称
    # =========================================
    model_name = os.getenv(
        "DASHSCOPE_EMBEDDING_MODEL",
        "qwen3.7-text-embedding",
    )

    # =========================================
    # 2. 创建 DashScope Embedding
    # =========================================
    return DashScopeEmbeddings(model=model_name)