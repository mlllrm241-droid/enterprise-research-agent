import json

from langchain_core.messages import HumanMessage, SystemMessage
from langsmith.evaluation import (
    EvaluationResult,
    EvaluationResults,
    run_evaluator,
)
from pydantic import BaseModel, Field

from app.core.model import get_model
from app.core.structured_output import parse_structured_output


class ReportQualityScore(BaseModel):
    requirement_coverage: int = Field(ge=1, le=5)
    analysis_quality: int = Field(ge=1, le=5)
    decision_usefulness: int = Field(ge=1, le=5)
    uncertainty_handling: int = Field(ge=1, le=5)
    comment: str


JUDGE_SYSTEM_PROMPT = """
你是企业研究报告质量评估员。

请根据用户原始研究需求，对报告进行质量评分。

评分维度：

1. requirement_coverage
是否完整覆盖用户要求。

2. analysis_quality
报告是否进行了有逻辑的比较、分析和归纳，
而非简单堆砌信息。

3. decision_usefulness
报告是否能帮助企业进行技术、采购或供应商决策。

4. uncertainty_handling
面对信息不足、数据冲突或证据不足时，
是否进行了明确说明。

每项1到5分。

注意：

不要判断Source ID是否真实存在，
这一点由程序化Evaluator负责。

不要因为报告篇幅长就给予高分。

只根据用户需求和报告内容评分。

仅输出符合JSON Schema的JSON。
"""


def score_report_quality(
    query: str,
    report: str,
) -> ReportQualityScore:
    # =========================================
    # 1. 创建 Judge Model
    # =========================================
    model = get_model()

    # =========================================
    # 2. 准备输出 Schema
    # =========================================
    schema = json.dumps(
        ReportQualityScore.model_json_schema(),
        ensure_ascii=False,
    )

    # =========================================
    # 3. 构建 Judge Prompt
    # =========================================
    prompt = f"""
用户需求：

{query}

研究报告：

{report[:16000]}

JSON Schema：

{schema}
"""

    # =========================================
    # 4. 调用 Judge
    # =========================================
    response = model.invoke([
        SystemMessage(
            content=JUDGE_SYSTEM_PROMPT
        ),
        HumanMessage(
            content=prompt
        ),
    ])

    # =========================================
    # 5. 解析结构化结果
    # =========================================
    return parse_structured_output(
        response.content,
        ReportQualityScore,
    )


@run_evaluator
def report_quality_judge(run, example):
    # =========================================
    # 1. 获取 Query 和 Report
    # =========================================
    outputs = run.outputs or {}
    inputs = example.inputs or {}

    query = inputs.get("query", "")
    report = outputs.get("report", "").strip()

    # =========================================
    # 2. 无报告直接返回0分
    # =========================================
    if not report:
        return EvaluationResults(
            results=[
                EvaluationResult(
                    key="judge_requirement_coverage",
                    score=0.0,
                    comment="未生成报告",
                ),
                EvaluationResult(
                    key="judge_analysis_quality",
                    score=0.0,
                    comment="未生成报告",
                ),
                EvaluationResult(
                    key="judge_decision_usefulness",
                    score=0.0,
                    comment="未生成报告",
                ),
                EvaluationResult(
                    key="judge_uncertainty_handling",
                    score=0.0,
                    comment="未生成报告",
                ),
            ]
        )

    # =========================================
    # 3. 创建 Judge Model
    # =========================================
    result = score_report_quality(
        query=query,
        report=report,
    )

    # =========================================
    # 6. 返回多个质量指标
    # =========================================
    return EvaluationResults(
        results=[
            EvaluationResult(
                key="judge_requirement_coverage",
                score=result.requirement_coverage / 5,
                comment=result.comment,
            ),
            EvaluationResult(
                key="judge_analysis_quality",
                score=result.analysis_quality / 5,
                comment=result.comment,
            ),
            EvaluationResult(
                key="judge_decision_usefulness",
                score=result.decision_usefulness / 5,
                comment=result.comment,
            ),
            EvaluationResult(
                key="judge_uncertainty_handling",
                score=result.uncertainty_handling / 5,
                comment=result.comment,
            ),
        ]
    )