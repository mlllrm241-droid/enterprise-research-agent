from pydantic import BaseModel, Field


class PlannedTask(BaseModel):
    """
    Planner 生成的一个研究子任务。
    """

    title: str = Field(
        description="子任务的简短标题"
    )

    description: str = Field(
        description="该子任务需要完成的具体研究内容"
    )


class ResearchPlan(BaseModel):
    """
    Planner 输出的完整研究计划。
    """

    goal: str = Field(
        description="整个研究任务的最终目标"
    )

    tasks: list[PlannedTask] = Field(
        min_length=3,
        max_length=6,
        description="完成研究目标所需的3到6个研究子任务"
    )