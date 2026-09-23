import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.model import get_model
from app.core.structured_output import parse_structured_output
from app.prompts.memory_prompt import MEMORY_SYSTEM_PROMPT
from app.schemas.memory import MemorySummary


def generate_memory_summary(
    user_query: str,
    report: str,
) -> MemorySummary:
    # =========================================
    # 1. 获取模型和 Schema
    # =========================================
    model = get_model()
    schema = json.dumps(MemorySummary.model_json_schema(), ensure_ascii=False)

    # =========================================
    # 2. 构建 Memory 请求
    # =========================================
    prompt = f"""
用户研究任务：
{user_query}

最终报告：
{report[:12000]}

请生成长期研究记忆。

JSON Schema：
{schema}
"""

    # =========================================
    # 3. 调用 MiMo
    # =========================================
    response = model.invoke([
        SystemMessage(content=MEMORY_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])

    # =========================================
    # 4. 解析 Memory
    # =========================================
    return parse_structured_output(
        response.content,
        MemorySummary,
    )