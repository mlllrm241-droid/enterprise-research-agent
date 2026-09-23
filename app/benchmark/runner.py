import json
import time
from pathlib import Path

from app.agents.baseline_agent import (
    build_baseline_agent,
)
from app.benchmark.schemas import (
    BenchmarkCase,
    BenchmarkResult,
)
from app.evaluation.evaluators import (
    agent_routing_f1,
    agent_routing_precision,
    agent_routing_recall,
    citation_validity,
    delivery_success,
    knowledge_evidence_usage,
    strict_task_success,
    todo_completion_rate,
)
from app.evaluation.llm_judge import (
    score_report_quality,
)
from app.evaluation.target import (
    run_research_target,
)


def load_benchmark_cases(
    path: str,
) -> list[BenchmarkCase]:
    data = json.loads(
        Path(path).read_text(
            encoding="utf-8",
        )
    )

    return [
        BenchmarkCase.model_validate(item)
        for item in data
    ]


def run_baseline(
    query: str,
) -> dict:
    # =========================================
    # 1. 创建 Baseline Agent
    # =========================================
    agent = build_baseline_agent()

    # =========================================
    # 2. 执行并记录耗时
    # =========================================
    started_at = time.perf_counter()

    result = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": query,
            }
        ]
    })

    latency = (
        time.perf_counter()
        - started_at
    )

    # =========================================
    # 3. 提取报告
    # =========================================
    messages = result.get(
        "messages",
        [],
    )

    report = ""

    if messages:
        content = messages[-1].content

        report = (
            content
            if isinstance(content, str)
            else str(content)
        )

    # =========================================
    # 4. 返回统一格式
    # =========================================
    return {
        "status": (
            "completed"
            if report.strip()
            else "failed"
        ),
        "review_status": None,
        "report": report,
        "todos": [],
        "agents_used": ["baseline"],
        "errors": [],
        "warnings": [],
        "source_ids": [],
        "knowledge_ids": [],
        "cited_source_ids": [],
        "cited_knowledge_ids": [],
        "latency_seconds": round(
            latency,
            2,
        ),
        "use_harness": None,
    }


def run_system(
    system: str,
    case: BenchmarkCase,
) -> dict:
    if system == "baseline":
        return run_baseline(
            case.query
        )

    if system == "full_no_harness":
        return run_research_target({
            "query": case.query,
            "use_harness": False,
        })

    if system == "full_harness":
        return run_research_target({
            "query": case.query,
            "use_harness": True,
        })

    raise ValueError(
        f"未知 Benchmark System：{system}"
    )


def build_benchmark_result(
    system: str,
    case: BenchmarkCase,
    raw: dict,
    with_judge: bool = False,
) -> BenchmarkResult:
    # =========================================
    # 1. 判断是否为 Baseline
    # =========================================
    is_baseline = system == "baseline"

    reference = case.model_dump()

    report = str(
        raw.get("report") or ""
    )

    errors = list(
        raw.get("errors") or []
    )

    # =========================================
    # 2. LLM Judge
    # =========================================
    judge_quality = None
    judge_error = None

    if with_judge and report.strip():
        try:
            quality = score_report_quality(
                query=case.query,
                report=report,
            )

            judge_quality = (
                quality.requirement_coverage
                + quality.analysis_quality
                + quality.decision_usefulness
                + quality.uncertainty_handling
            ) / 20

        except Exception as exc:
            judge_error = (
                f"{type(exc).__name__}: {exc}"
            )

    # =========================================
    # 3. Baseline 不适用的指标返回 None
    # =========================================
    if is_baseline:
        return BenchmarkResult(
            case_id=case.case_id,
            category=case.category,
            system=system,
            status=str(
                raw.get("status") or "failed"
            ),
            review_status=None,
            use_harness=None,
            benchmark_timeout=bool(
                raw.get(
                    "benchmark_timeout",
                    False,
                )
            ),
            delivery_success=float(
                delivery_success(raw)
            ),
            strict_task_success=None,
            todo_completion_rate=None,
            citation_validity=None,
            knowledge_evidence_usage=None,
            routing_precision=None,
            routing_recall=None,
            routing_f1=None,
            reviewer_passed=None,
            llm_judge_quality=judge_quality,
            judge_error=judge_error,
            model_limit_failures=None,
            total_errors=len(errors),
            latency_seconds=float(
                raw.get(
                    "latency_seconds",
                    0,
                )
                or 0
            ),
            report=report,
        )

    # =========================================
    # 4. Full Agent 指标
    # =========================================
    model_limit_count = sum(
        "ModelCallLimitExceededError"
        in error
        for error in errors
    )

    source_validity = (
        float(
            citation_validity(
                raw,
                reference,
            )
        )
        if case.requires_sources
        else None
    )

    knowledge_usage = (
        float(
            knowledge_evidence_usage(
                raw,
                reference,
            )
        )
        if case.requires_knowledge
        else None
    )

    return BenchmarkResult(
        case_id=case.case_id,
        category=case.category,
        system=system,
        status=str(
            raw.get("status") or "failed"
        ),
        review_status=raw.get(
            "review_status"
        ),
        use_harness=bool(
            raw.get(
                "use_harness",
                system == "full_harness",
            )
        ),
        benchmark_timeout=bool(
            raw.get(
                "benchmark_timeout",
                False,
            )
        ),
        delivery_success=float(
            delivery_success(raw)
        ),
        strict_task_success=float(
            strict_task_success(raw)
        ),
        todo_completion_rate=float(
            todo_completion_rate(raw)
        ),
        citation_validity=source_validity,
        knowledge_evidence_usage=(
            knowledge_usage
        ),
        routing_precision=float(
            agent_routing_precision(
                raw,
                reference,
            )
        ),
        routing_recall=float(
            agent_routing_recall(
                raw,
                reference,
            )
        ),
        routing_f1=float(
            agent_routing_f1(
                raw,
                reference,
            )
        ),
        reviewer_passed=float(
            raw.get("review_status")
            == "passed"
        ),
        llm_judge_quality=judge_quality,
        judge_error=judge_error,
        model_limit_failures=(
            model_limit_count
        ),
        total_errors=len(errors),
        latency_seconds=float(
            raw.get(
                "latency_seconds",
                0,
            )
            or 0
        ),
        report=report,
    )