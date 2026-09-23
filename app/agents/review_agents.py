import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.model import get_model
from app.core.structured_output import parse_structured_output
from app.prompts.review_prompts import (
    REPLANNER_SYSTEM_PROMPT,
    REVIEWER_SYSTEM_PROMPT,
)
from app.schemas.review import ReplanDecision, ReviewResult


def review_research(review_context: str) -> ReviewResult:
    # =========================================
    # 1. 获取模型和 Schema
    # =========================================
    model = get_model()
    schema = json.dumps(ReviewResult.model_json_schema(), ensure_ascii=False)

    # =========================================
    # 2. 构建 Review 请求
    # =========================================
    prompt = f"""
下面是当前企业研究任务的完整审查材料：

{review_context}

输出要求：
1. 只能输出一个 JSON 对象。
2. 禁止 Markdown 代码块。
3. 必须满足下面的 JSON Schema。

JSON Schema：
{schema}
"""

    # =========================================
    # 3. 调用 MiMo Reviewer
    # =========================================
    response = model.invoke([
        SystemMessage(content=REVIEWER_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])

    # =========================================
    # 4. 解析 ReviewResult
    # =========================================
    return parse_structured_output(response.content, ReviewResult)


def generate_replan(replan_context: str) -> ReplanDecision:
    # =========================================
    # 1. 获取模型和 Schema
    # =========================================
    model = get_model()
    schema = json.dumps(ReplanDecision.model_json_schema(), ensure_ascii=False)

    # =========================================
    # 2. 构建 Replan 请求
    # =========================================
    prompt = f"""
下面是当前任务和 Reviewer 的反馈：

{replan_context}

请制定最小必要的修复计划。

输出要求：
1. 只能输出一个 JSON 对象。
2. 禁止 Markdown 代码块。
3. 必须满足下面的 JSON Schema。

JSON Schema：
{schema}
"""

    # =========================================
    # 3. 调用 MiMo Replanner
    # =========================================
    response = model.invoke([
        SystemMessage(content=REPLANNER_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])

    # =========================================
    # 4. 解析 ReplanDecision
    # =========================================
    return parse_structured_output(response.content, ReplanDecision)