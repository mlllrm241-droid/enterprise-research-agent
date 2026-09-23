from typing import Literal

from langgraph.types import interrupt

from app.states.research_state import EnterpriseResearchState
from app.workspace.manager import TaskWorkspace


def prepare_human_review_node(
    state: EnterpriseResearchState,
) -> dict:
    # =========================================
    # 1. 获取 Workspace
    # =========================================
    workspace = TaskWorkspace(
        state["task_id"]
    )

    # =========================================
    # 2. 更新 task.json
    # =========================================
    task_info = workspace.read_json(
        "task.json"
    )

    task_info.update({
        "status": "waiting_human",
        "human_review_status": "waiting",
        "report_path": state["final_report_path"],
    })

    workspace.write_json(
        "task.json",
        task_info,
    )

    # =========================================
    # 3. 更新 Graph State
    # =========================================
    return {
        "status": "waiting_human",
        "human_review_status": "waiting",
        "current_step": "waiting_human_review",
    }


def human_review_node(
    state: EnterpriseResearchState,
) -> dict:
    # =========================================
    # 1. 暂停 Graph，等待人工决策
    # =========================================
    decision = interrupt({
        "type": "report_approval",
        "task_id": state["task_id"],
        "report_path": state["final_report_path"],
        "review_status": state["review_status"],
        "review_summary": state["last_review_summary"],
        "allowed_actions": [
            "approve",
            "revise",
            "reject",
        ],
    })

    # =========================================
    # 2. 解析人工决策
    # =========================================
    action = decision.get("action")
    feedback = decision.get(
        "feedback",
        "",
    ).strip()

    if action not in {
        "approve",
        "revise",
        "reject",
    }:
        raise ValueError(
            f"非法人工审批动作：{action}"
        )

    # =========================================
    # 3. 计算审批轮次
    # =========================================
    review_round = (
        state["human_review_round"] + 1
    )

    # =========================================
    # 4. 保存人工审批记录
    # =========================================
    workspace = TaskWorkspace(
        state["task_id"]
    )

    artifact_path = (
        f"reviews/"
        f"human_review_{review_round}.json"
    )

    workspace.write_json(
        artifact_path,
        {
            "round": review_round,
            "action": action,
            "feedback": feedback,
            "report_path": state["final_report_path"],
        },
    )

    # =========================================
    # 5. 映射 Human Review 状态
    # =========================================
    status_map = {
        "approve": "approved",
        "revise": "revision_requested",
        "reject": "rejected",
    }

    # =========================================
    # 6. 更新 State
    # =========================================
    return {
        "human_review_round": review_round,
        "human_review_status": status_map[action],
        "human_feedback": feedback or None,
        "human_review_artifacts": [artifact_path],
        "current_step": f"human_{action}",
    }


def apply_human_revision_node(
    state: EnterpriseResearchState,
) -> dict:
    # =========================================
    # 1. 获取人工修改意见
    # =========================================
    feedback = state["human_feedback"]

    if not feedback:
        raise ValueError(
            "人工要求修改，但没有提供反馈"
        )

    # =========================================
    # 2. 生成新的 Todo ID
    # =========================================
    max_id = max(
        (int(todo["id"][1:]) for todo in state["todos"]),
        default=0,
    )

    todo_id = f"T{max_id + 1:02d}"

    # =========================================
    # 3. 创建人工补充 Todo
    # =========================================
    new_todo = {
        "id": todo_id,
        "title": "人工复核要求的补充研究",
        "description": feedback,
        "status": "pending",

        "assigned_agent": None,
        "assignment_reason": None,

        "artifact_path": None,
        "source_artifact_path": None,
        "knowledge_artifact_path": None,
    }

    # =========================================
    # 4. 更新 Todo List
    # =========================================
    todos = [
        *state["todos"],
        new_todo,
    ]

    # =========================================
    # 5. 恢复任务执行状态
    # =========================================
    return {
        "todos": todos,
        "status": "running",
        "human_review_status": "not_requested",
        "auto_replan_round": 0,     # 人工干预后开启新的自动修复周期
        "current_todo_id": None,
        "current_agent": None,
        "current_step": f"human_revision_{todo_id}",
    }


def route_after_human_review(
    state: EnterpriseResearchState,
) -> Literal[
    "approve",
    "revise",
    "reject",
]:
    # =========================================
    # 1. 人工批准
    # =========================================
    if state["human_review_status"] == "approved":
        return "approve"

    # =========================================
    # 2. 人工要求修改
    # =========================================
    if state["human_review_status"] == "revision_requested":
        return "revise"

    # =========================================
    # 3. 人工拒绝
    # =========================================
    return "reject"