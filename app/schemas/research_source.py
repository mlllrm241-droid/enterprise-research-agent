from pydantic import BaseModel, Field


class ResearchSource(BaseModel):
    """
    标准化研究来源。
    """

    source_id: str = Field(
        description="当前研究任务中的唯一来源ID"
    )

    title: str

    url: str

    snippet: str

    score: float | None = None

    published_at: str | None = None

    query: str

    topic: str

    retrieved_at: str