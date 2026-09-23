from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.research import router as research_router
from app.graphs.research_graph import (
    build_research_graph,
)
from app.runtime.task_manager import (
    ResearchTaskManager,
)

from dotenv import load_dotenv

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # =========================================
    # 1. 构建共享 Research Graph
    # =========================================
    graph = build_research_graph()

    # =========================================
    # 2. 初始化 Task Manager
    # =========================================
    app.state.task_manager = (
        ResearchTaskManager(graph)
    )

    # =========================================
    # 3. 启动 FastAPI
    # =========================================
    yield

    # =========================================
    # 4. 清理后台 Task
    # =========================================
    await app.state.task_manager.shutdown()


app = FastAPI(
    title="Enterprise Research Agent API",
    version="0.13.0",
    lifespan=lifespan,
)

app.include_router(
    health_router
)

app.include_router(
    research_router,
    prefix="/api/v1",
)