from typing import Literal

from pydantic import BaseModel, Field


BenchmarkCategory = Literal[
    "company",
    "market",
    "finance",
    "risk",
    "general",
]


class BenchmarkCase(BaseModel):
    case_id: str
    category: BenchmarkCategory
    query: str

    expected_agents: list[str] = Field(
        default_factory=list,
    )

    requires_sources: bool = True
    requires_knowledge: bool = False


class BenchmarkResult(BaseModel):
    case_id: str
    category: str
    system: str

    status: str
    review_status: str | None = None
    use_harness: bool | None = None

    benchmark_timeout: bool = False

    delivery_success: float
    strict_task_success: float | None = None
    todo_completion_rate: float | None = None

    citation_validity: float | None = None
    knowledge_evidence_usage: float | None = None

    routing_precision: float | None = None
    routing_recall: float | None = None
    routing_f1: float | None = None

    reviewer_passed: float | None = None
    llm_judge_quality: float | None = None
    judge_error: str | None = None

    model_limit_failures: int | None = None
    total_errors: int = 0
    latency_seconds: float

    report: str = ""