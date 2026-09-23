from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.responses import PlainTextResponse
from fastapi.sse import (
    EventSourceResponse,
    ServerSentEvent,
)

from app.api.dependencies import (
    get_task_manager,
)
from app.api.schemas.research import (
    HumanReviewRequest,
    HumanReviewResponse,
    ResearchTaskCreate,
    ResearchTaskCreated,
    ResearchTaskStatus,
)
from app.runtime.task_manager import (
    ResearchTaskManager,
)
from app.workspace.manager import (
    TaskWorkspace,
)


router = APIRouter(
    prefix="/research",
    tags=["Research"],
)


TaskManagerDep = Annotated[
    ResearchTaskManager,
    Depends(get_task_manager),
]


@router.post(
    "/tasks",
    response_model=ResearchTaskCreated,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_research_task(
    request: ResearchTaskCreate,
    manager: TaskManagerDep,
):
    # =========================================
    # 1. 创建后台研究任务
    # =========================================
    task_id = await manager.create_task(
        query=request.query,
        user_id=request.user_id,
    )

    # =========================================
    # 2. 立即返回 Task ID
    # =========================================
    return ResearchTaskCreated(
        task_id=task_id,
        status="created",
    )


@router.get(
    "/tasks/{task_id}",
    response_model=ResearchTaskStatus,
)
async def get_research_task(
    task_id: str,
    manager: TaskManagerDep,
):
    # =========================================
    # 1. 获取 Graph State
    # =========================================
    try:
        state = manager.get_state(
            task_id
        )

    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="研究任务不存在",
        )

    # =========================================
    # 2. 返回状态
    # =========================================
    return ResearchTaskStatus(
        task_id=task_id,
        status=state["status"],
        current_step=state.get(
            "current_step"
        ),
        current_todo_id=state.get(
            "current_todo_id"
        ),
        current_agent=state.get(
            "current_agent"
        ),
        review_status=state.get(
            "review_status"
        ),
        human_review_status=state.get(
            "human_review_status"
        ),
        final_report_path=state.get(
            "final_report_path"
        ),
        todos=state.get(
            "todos",
            [],
        ),
        errors=state.get(
            "errors",
            [],
        ),
        warnings=state.get(
            "warnings",
            [],
        ),
    )


@router.get(
    "/tasks/{task_id}/events",
    response_class=EventSourceResponse,
)
async def stream_research_events(
    task_id: str,
    manager: TaskManagerDep,
):
    try:
        manager.get_state(task_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="研究任务不存在",
        )

    event_id = 1

    async for event in manager.stream_events(task_id):
        yield ServerSentEvent(
            data=event,
            event=event.get("type", "progress"),
            id=str(event_id),
        )

        event_id += 1


@router.post(
    "/tasks/{task_id}/review",
    response_model=HumanReviewResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def review_research_task(
    task_id: str,
    request: HumanReviewRequest,
    manager: TaskManagerDep,
):
    # =========================================
    # 1. 获取 Task State
    # =========================================
    try:
        state = manager.get_state(
            task_id
        )

    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="研究任务不存在",
        )

    # =========================================
    # 2. 检查是否正在等待 Human Review
    # =========================================
    if (
        state.get(
            "human_review_status"
        )
        != "waiting"
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "任务当前不处于人工审核状态"
            ),
        )

    # =========================================
    # 3. Resume LangGraph
    # =========================================
    try:
        await manager.resume_task(
            task_id=task_id,
            action=request.action,
            feedback=request.feedback,
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        )

    # =========================================
    # 4. 返回 Resume 状态
    # =========================================
    return HumanReviewResponse(
        task_id=task_id,
        action=request.action,
        status="resumed",
    )


@router.get(
    "/tasks/{task_id}/report",
    response_class=PlainTextResponse,
)
async def get_research_report(
    task_id: str,
    manager: TaskManagerDep,
):
    # =========================================
    # 1. 获取 Task State
    # =========================================
    try:
        state = manager.get_state(
            task_id
        )

    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="研究任务不存在",
        )

    # =========================================
    # 2. 获取报告路径
    # =========================================
    report_path = state.get(
        "final_report_path"
    )

    if not report_path:
        raise HTTPException(
            status_code=404,
            detail="当前任务尚未生成报告",
        )

    # =========================================
    # 3. 读取 Workspace Report
    # =========================================
    workspace = TaskWorkspace(
        task_id
    )

    if not workspace.exists(
        report_path
    ):
        raise HTTPException(
            status_code=404,
            detail="报告文件不存在",
        )

    # =========================================
    # 4. 返回 Markdown
    # =========================================
    return PlainTextResponse(
        workspace.read_text(
            report_path
        ),
        media_type=(
            "text/markdown; charset=utf-8"
        ),
    )