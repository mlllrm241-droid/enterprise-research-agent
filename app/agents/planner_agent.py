import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.model import get_model
from app.core.structured_output import parse_structured_output
from app.prompts.planner_prompt import PLANNER_SYSTEM_PROMPT
from app.schemas.research_plan import ResearchPlan


def generate_research_plan(
    user_query: str,
    memory_context: str = "",
) -> ResearchPlan:
    # =========================================
    # 1. 获取模型和 JSON Schema
    # =========================================
    model = get_model()
    schema = json.dumps(
        ResearchPlan.model_json_schema(),
        ensure_ascii=False,
    )

    # =========================================
    # 2. 构建 Planner 输入
    # =========================================
    prompt = f"""
用户研究需求：

{user_query}

长期记忆：

{memory_context or "无"}

请制定研究计划。

长期记忆使用规则：

1. 当前用户请求永远优先。
2. 用户长期偏好可以影响报告形式和研究方式。
3. 历史 Research Episode 只能作为研究背景。
4. 历史事实不得直接当作本次事实证据。
5. 涉及当前事实仍然必须通过本次工具重新验证。

输出要求：
1. 只能输出一个 JSON 对象。
2. 禁止输出 JSON 数组。
3. 禁止输出 Markdown 代码块。
4. 必须满足下面的 JSON Schema。

JSON Schema：

{schema}
"""

    # =========================================
    # 3. 调用 MiMo
    # =========================================
    response = model.invoke([
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])

    # =========================================
    # 4. 解析 ResearchPlan
    # =========================================
    return parse_structured_output(
        response.content,
        ResearchPlan,
    )