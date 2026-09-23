
from app.schemas.subagent_route import SubagentRoute
from app.states.research_state import EnterpriseResearchState

from app.agents.supervisor_agent import select_subagent


def assign_subagent_node(state: EnterpriseResearchState) -> dict:
    # =========================================
    # 1. 获取当前 Todo
    # =========================================
    todo_id = state["current_todo_id"]
    todo = next((item for item in state["todos"] if item["id"] == todo_id), None)

    if todo is None:
        return {
            "current_agent": "general",
            "current_step": "assign_general",
        }

    # =========================================
    # 2. Supervisor 选择专业 Agent
    # =========================================
    try:
        # =========================================
        # 2. Supervisor 选择专业 Agent
        # =========================================
        route = select_subagent(
            user_query=state["user_query"],
            todo_title=todo["title"],
            todo_description=todo["description"],
        )

    except Exception as e:
        route = SubagentRoute(
            agent="general",
            reason=f"Supervisor 路由失败，使用 General Agent：{e}",
        )

    # =========================================
    # 3. 更新 Todo Assignment
    # =========================================
    updated_todos = [
        {
            **item,
            "assigned_agent": route.agent,
            "assignment_reason": route.reason,
        }
        if item["id"] == todo_id else item
        for item in state["todos"]
    ]

    # =========================================
    # 4. 更新当前执行 Agent
    # =========================================
    return {
        "todos": updated_todos,
        "current_agent": route.agent,
        "current_step": f"assigned_{route.agent}_{todo_id}",
    }