from fastapi import Request

from app.runtime.task_manager import (
    ResearchTaskManager,
)


def get_task_manager(
    request: Request,
) -> ResearchTaskManager:
    # =========================================
    # 1. 获取共享 Task Manager
    # =========================================
    return request.app.state.task_manager