from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ResearchTaskCreate(BaseModel):
    query: str = Field(
        min_length=5,
        description="企业研究任务",
    )

    user_id: str = Field(
        default="local_user",
        min_length=1,
    )


class ResearchTaskCreated(BaseModel):
    task_id: str
    status: str


class HumanReviewRequest(BaseModel):
    action: Literal[
        "approve",
        "revise",
        "reject",
    ]

    feedback: str = ""

    @model_validator(mode="after")
    def validate_feedback(self):
        # =========================================
        # 1. revise 必须提供修改意见
        # =========================================
        if (
            self.action == "revise"
            and not self.feedback.strip()
        ):
            raise ValueError(
                "revise 操作必须提供 feedback"
            )

        return self


class HumanReviewResponse(BaseModel):
    task_id: str
    action: str
    status: str


class ResearchTaskStatus(BaseModel):
    task_id: str
    status: str
    current_step: str | None = None

    current_todo_id: str | None = None
    current_agent: str | None = None

    review_status: str | None = None
    human_review_status: str | None = None

    final_report_path: str | None = None

    todos: list[dict] = Field(
        default_factory=list
    )

    errors: list[str] = Field(
        default_factory=list
    )

    warnings: list[str] = Field(
        default_factory=list
    )