import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.model import get_model
from app.core.structured_output import parse_structured_output
from app.prompts.supervisor_prompt import SUPERVISOR_SYSTEM_PROMPT
from app.schemas.subagent_route import SubagentRoute


def select_subagent(
    user_query: str,
    todo_title: str,
    todo_description: str,
) -> SubagentRoute:

    # =========================================
    # 1. 获取模型和 JSON Schema
    # =========================================
    model = get_model()
    schema = json.dumps(
        SubagentRoute.model_json_schema(),
        ensure_ascii=False,
    )

    # =========================================
    # 2. 构建路由任务
    # =========================================
    prompt = f"""
原始研究任务：
{user_query}

当前 Todo：
标题：{todo_title}
任务：{todo_description}

请选择最合适的 Subagent。

输出要求：
1. 只能返回一个 JSON 对象。
2. 禁止返回 JSON 数组。
3. 禁止使用 Markdown 代码块。
4. 必须满足下面的 JSON Schema。

JSON Schema：

{schema}
"""

    # =========================================
    # 3. 调用 MiMo
    # =========================================
    response = model.invoke([
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])

    # =========================================
    # 4. 解析 SubagentRoute
    # =========================================
    return parse_structured_output(
        response.content,
        SubagentRoute,
    )