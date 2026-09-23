from pydantic import BaseModel, Field


class UserMemoryProfile(BaseModel):
    language: str = "zh-CN"
    source_preferences: list[str] = Field(default_factory=list)
    report_preferences: list[str] = Field(default_factory=list)


class MemorySummary(BaseModel):
    summary: str
    topics: list[str] = Field(default_factory=list, max_length=8)


class ResearchEpisode(BaseModel):
    task_id: str
    user_query: str
    summary: str
    topics: list[str]
    review_status: str
    final_report_path: str
    created_at: str