import asyncio
from typing import Any

from langgraph.types import Command

from app.states.research_state import (
    create_initial_state,
)


TERMINAL_STATUSES = {
    "completed",
    "completed_with_warnings",
    "failed",
    "rejected",
}


class ResearchTaskManager:
    def __init__(self, graph):
        # =========================================
        # 1. 保存 Research Graph
        # =========================================
        self.graph = graph

        # =========================================
        # 2. 保存后台运行任务
        # =========================================
        self.running_tasks: dict[
            str,
            asyncio.Task,
        ] = {}

        # =========================================
        # 3. 保存 SSE Event Queue
        # =========================================
        self.event_queues: dict[
            str,
            asyncio.Queue,
        ] = {}

        # =========================================
        # 4. 保存最新 Task State
        # =========================================
        self.latest_states: dict[
            str,
            dict,
        ] = {}

    def _get_config(
        self,
        task_id: str,
    ) -> dict:
        # =========================================
        # 1. 构建 LangGraph Config
        # =========================================
        return {
            "configurable": {
                "thread_id": task_id,
            },
            "recursion_limit": 100,
        }

    def _get_queue(
        self,
        task_id: str,
    ) -> asyncio.Queue:
        # =========================================
        # 1. 获取或创建 Event Queue
        # =========================================
        if task_id not in self.event_queues:
            self.event_queues[
                task_id
            ] = asyncio.Queue()

        return self.event_queues[
            task_id
        ]

    async def create_task(
        self,
        query: str,
        user_id: str,
    ) -> str:
        # =========================================
        # 1. 创建初始 State
        # =========================================
        initial_state = create_initial_state(
            user_query=query,
            user_id=user_id,
        )

        task_id = initial_state[
            "task_id"
        ]

        # =========================================
        # 2. 立即缓存初始 State
        # =========================================
        self.latest_states[
            task_id
        ] = dict(initial_state)

        # =========================================
        # 3. 初始化 Event Queue
        # =========================================
        self._get_queue(
            task_id
        )

        # =========================================
        # 4. 后台运行 Graph
        # =========================================
        task = asyncio.create_task(
            self._execute_graph(
                task_id,
                initial_state,
            )
        )

        self.running_tasks[
            task_id
        ] = task

        # =========================================
        # 5. 返回 Task ID
        # =========================================
        return task_id

    async def resume_task(
        self,
        task_id: str,
        action: str,
        feedback: str = "",
    ) -> None:
        # =========================================
        # 1. 防止同一 Task 重复运行
        # =========================================
        running = self.running_tasks.get(
            task_id
        )

        if (
            running
            and not running.done()
        ):
            raise RuntimeError(
                "任务当前仍在运行"
            )

        # =========================================
        # 2. 构建 Human Resume Command
        # =========================================
        command = Command(
            resume={
                "action": action,
                "feedback": feedback,
            }
        )

        # =========================================
        # 3. 后台恢复 Graph
        # =========================================
        task = asyncio.create_task(
            self._execute_graph(
                task_id,
                command,
            )
        )

        self.running_tasks[
            task_id
        ] = task

    async def _execute_graph(
        self,
        task_id: str,
        graph_input: Any,
    ) -> None:
        # =========================================
        # 1. 获取 Event Loop
        # =========================================
        loop = asyncio.get_running_loop()

        # =========================================
        # 2. 在线程中运行同步 Graph
        # =========================================
        try:
            await asyncio.to_thread(
                self._stream_graph_sync,
                task_id,
                graph_input,
                loop,
            )

        except Exception as e:
            # =========================================
            # 3. 发布运行异常
            # =========================================
            queue = self._get_queue(
                task_id
            )

            await queue.put({
                "type": "error",
                "task_id": task_id,
                "error": (
                    f"{type(e).__name__}: {e}"
                ),
            })

        finally:
            # =========================================
            # 4. 清理后台任务引用
            # =========================================
            self.running_tasks.pop(
                task_id,
                None,
            )

    def _stream_graph_sync(
        self,
        task_id: str,
        graph_input: Any,
        loop,
    ) -> None:
        # =========================================
        # 1. 获取 Graph Config
        # =========================================
        config = self._get_config(
            task_id
        )

        queue = self._get_queue(
            task_id
        )

        # =========================================
        # 2. Stream Graph State
        # =========================================
        for state in self.graph.stream(
            graph_input,
            config=config,
            stream_mode="values",
        ):
            # =========================================
            # 3. 更新最新 State 缓存
            # =========================================
            self.latest_states[
                task_id
            ] = dict(state)

            # =========================================
            # 4. 构建 SSE Event
            # =========================================
            event = self._build_event(
                state
            )

            loop.call_soon_threadsafe(
                queue.put_nowait,
                event,
            )

    def _build_event(
        self,
        state: dict,
    ) -> dict:
        # =========================================
        # 1. 构建轻量 Progress Event
        # =========================================
        return {
            "type": "progress",
            "task_id": state.get(
                "task_id"
            ),
            "status": state.get(
                "status"
            ),
            "current_step": state.get(
                "current_step"
            ),
            "current_todo_id": state.get(
                "current_todo_id"
            ),
            "current_agent": state.get(
                "current_agent"
            ),
            "review_status": state.get(
                "review_status"
            ),
            "human_review_status": state.get(
                "human_review_status"
            ),
            "final_report_path": state.get(
                "final_report_path"
            ),
            "todos": state.get(
                "todos",
                [],
            ),
        }

    def get_state(
        self,
        task_id: str,
    ) -> dict:
        # =========================================
        # 1. 构建 LangGraph Config
        # =========================================
        config = self._get_config(
            task_id
        )

        # =========================================
        # 2. 优先读取 SQLite Checkpoint
        # =========================================
        snapshot = self.graph.get_state(
            config
        )

        if snapshot.values:
            state = dict(
                snapshot.values
            )

            self.latest_states[
                task_id
            ] = state

            return state

        # =========================================
        # 3. Checkpoint 尚未生成时读取内存缓存
        # =========================================
        if task_id in self.latest_states:
            return dict(
                self.latest_states[
                    task_id
                ]
            )

        # =========================================
        # 4. Task 确实不存在
        # =========================================
        raise KeyError(
            f"任务不存在：{task_id}"
        )

    async def stream_events(
        self,
        task_id: str,
    ):
        # =========================================
        # 1. 检查 Task
        # =========================================
        self.get_state(
            task_id
        )

        queue = self._get_queue(
            task_id
        )

        # =========================================
        # 2. 持续消费 Event
        # =========================================
        while True:
            event = await queue.get()

            yield event

            # =========================================
            # 3. Human Review 时暂停 SSE
            # =========================================
            if (
                event.get("status")
                == "waiting_human"
            ):
                break

            # =========================================
            # 4. Terminal Status 时结束
            # =========================================
            if event.get(
                "status"
            ) in TERMINAL_STATUSES:
                break

            # =========================================
            # 5. Error Event
            # =========================================
            if (
                event.get("type")
                == "error"
            ):
                break

    async def shutdown(self):
        # =========================================
        # 1. 取消仍在运行的后台任务
        # =========================================
        tasks = [
            task
            for task in self.running_tasks.values()
            if not task.done()
        ]

        for task in tasks:
            task.cancel()

        # =========================================
        # 2. 等待任务退出
        # =========================================
        if tasks:
            await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )