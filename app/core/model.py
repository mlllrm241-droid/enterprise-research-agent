import os

from langchain_openai import ChatOpenAI


def get_model(max_retries: int = 2):
    # =========================================
    # 1. 读取 MiMo 配置
    # =========================================
    api_key = os.getenv("MIMO_API_KEY")
    base_url = os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
    model_name = os.getenv("MIMO_MODEL", "mimo-v2.5-pro")

    if not api_key:
        raise ValueError("缺少 MIMO_API_KEY")

    # =========================================
    # 2. 创建 MiMo 模型
    # =========================================
    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        max_retries=max_retries,
        timeout=120,
        use_responses_api=False,
        extra_body={"thinking": {"type": "disabled"}},
    )