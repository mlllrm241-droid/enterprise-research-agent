from datetime import datetime, timezone

from app.agents.memory_agent import generate_memory_summary
from app.memory.service import LongTermMemoryService
from app.schemas.memory import ResearchEpisode
from app.states.research_state import EnterpriseResearchState
from app.workspace.manager import TaskWorkspace


def load_long_term_memory_node(
    state: EnterpriseResearchState,
) -> dict:
    # =========================================
    # 1. Evaluation 模式不读取长期记忆
    # =========================================
    if state.get("evaluation_mode", False):
        return {
            "memory_context": "",
            "retrieved_memory_ids": [],
            "current_step": "memory_skipped_eval",
        }

    try:
        # =========================================
        # 1. 初始化 Memory Service
        # =========================================
        service = LongTermMemoryService(
            state["user_id"]
        )

        # =========================================
        # 2. 检索用户长期记忆
        # =========================================
        context, memory_ids = service.build_memory_context(
            state["user_query"]
        )

        # =========================================
        # 3. 更新 State
        # =========================================
        return {
            "memory_context": context,
            "retrieved_memory_ids": memory_ids,
            "current_step": "memory_loaded",
        }

    except Exception as e:
        # =========================================
        # 4. Memory 失败时降级
        # =========================================
        return {
            "memory_context": "",
            "retrieved_memory_ids": [],
            "warnings": [
                f"长期记忆加载失败：{type(e).__name__}: {e}"
            ],
            "current_step": "memory_load_failed",
        }


def save_long_term_memory_node(
    state: EnterpriseResearchState,
) -> dict:
    try:
        # =========================================
        # 1. 检查最终报告
        # =========================================
        if not state["final_report_path"]:
            return {"current_step": "memory_save_skipped"}

        # =========================================
        # 2. 读取最终报告
        # =========================================
        workspace = TaskWorkspace(state["task_id"])
        report = workspace.read_text(state["final_report_path"])

        # =========================================
        # 3. 生成 Episode Summary
        # =========================================
        summary = generate_memory_summary(
            state["user_query"],
            report,
        )

        # =========================================
        # 4. 构建 Research Episode
        # =========================================
        episode = ResearchEpisode(
            task_id=state["task_id"],
            user_query=state["user_query"],
            summary=summary.summary,
            topics=summary.topics,
            review_status=state["review_status"],
            final_report_path=state["final_report_path"],
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # =========================================
        # 5. 保存长期记忆
        # =========================================
        service = LongTermMemoryService(state["user_id"])
        service.store.save_episode(episode)

        # =========================================
        # 6. 更新 State
        # =========================================
        return {
            "status": "running",
            "stored_memory_ids": [state["task_id"]],
            "current_step": "memory_saved",
        }

    except Exception as e:
        # =========================================
        # 7. Memory 写入失败时降级
        # =========================================
        return {
            "warnings": [
                f"长期记忆保存失败：{type(e).__name__}: {e}"
            ],
            "current_step": "memory_save_failed",
        }