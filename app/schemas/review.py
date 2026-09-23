from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.research_plan import PlannedTask


IssueCategory = Literal[
    "missing_requirement",
    "insufficient_evidence",
    "invalid_citation",
    "contradiction",
    "failed_todo",
    "other",
]

IssuePriority = Literal[
    "high",
    "medium",
    "low",
]


class ReviewIssue(BaseModel):
    category: IssueCategory
    priority: IssuePriority
    description: str
    related_todo_ids: list[str] = Field(default_factory=list)
    suggested_action: str


class ReviewResult(BaseModel):
    passed: bool
    summary: str
    issues: list[ReviewIssue] = Field(default_factory=list)


class ReplanDecision(BaseModel):
    reason: str

    retry_todo_ids: list[str] = Field(
        default_factory=list,
        description="需要重新执行的失败 Todo ID",
    )

    new_tasks: list[PlannedTask] = Field(
        default_factory=list,
        max_length=3,
        description="需要新增的补充研究任务",
    )