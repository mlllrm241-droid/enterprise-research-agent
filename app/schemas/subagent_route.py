from typing import Literal

from pydantic import BaseModel, Field


AgentType = Literal[
    "company",
    "market",
    "finance",
    "risk",
    "general",
]


class SubagentRoute(BaseModel):
    agent: AgentType

    reason: str = Field(
        description="选择该 Subagent 的简短原因"
    )