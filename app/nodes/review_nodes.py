import json

from typing import Literal

from app.agents.review_agents import generate_replan, review_research
from app.states.research_state import EnterpriseResearchState
from app.workspace.manager import TaskWorkspace


def _build_review_context(state: EnterpriseResearchState) -> str:
    # =========================================
    # 1. 获取 Workspace
    # =========================================
    workspace = TaskWorkspace(state["task_id"])

    # =========================================
    # 2. 读取当前报告
    # =========================================
    report = ""
    if state["final_report_path"]:
        report = workspace.read_text(state["final_report_path"])

    # =========================================
    # 3. 读取 Research Artifacts
    # =========================================
    research_parts = []

    for todo in state["todos"]:
        if todo["artifact_path"] and workspace.exists(todo["artifact_path"]):
            research_parts.append(workspace.read_text(todo["artifact_path"]))

    # =========================================
    # 4. 读取 External Sources
    # =========================================
    source_parts = []

    for path in state["source_artifacts"]:
        if workspace.exists(path):
            source_parts.append(
                json.dumps(workspace.read_json(path), ensure_ascii=False)
            )

    # =========================================
    # 5. 读取 Internal Evidence
    # =========================================
    knowledge_parts = []

    for path in state["knowledge_artifacts"]:
        if workspace.exists(path):
            knowledge_parts.append(
                json.dumps(workspace.read_json(path), ensure_ascii=False)
            )

    # =========================================
    # 6. 构建 Todo 状态
    # =========================================
    todo_context = json.dumps(state["todos"], ensure_ascii=False)

    # =========================================
    # 7. 返回 Review Context
    # =========================================
    return f"""
用户原始需求：
{state["user_query"]}

研究目标：
{state["plan_goal"]}

Todo 状态：
{todo_context}

当前报告：
{report}

Research Artifacts：
{"\n\n".join(research_parts)}

External Source Index：
{"\n\n".join(source_parts)}

Internal Knowledge Evidence：
{"\n\n".join(knowledge_parts)}
"""

def review_report_node(state: EnterpriseResearchState) -> dict:
    try:
        # =========================================
        # 1. 构建 Review Context
        # =========================================
        review_context = _build_review_context(state)

        # =========================================
        # 2. 执行 Reviewer
        # =========================================
        review = review_research(review_context)

        # =========================================
        # 3. 更新全局 Review Round
        # =========================================
        review_round = state["review_round"] + 1

        # =========================================
        # 4. 更新自动 Replan Round
        # =========================================
        auto_replan_round = state["auto_replan_round"] + 1

        # =========================================
        # 5. 整理 Review Issues
        # =========================================
        issues = []

        for index, issue in enumerate(review.issues, start=1):
            item = issue.model_dump()
            item["issue_id"] = f"R{review_round}-I{index:02d}"
            issues.append(item)

        # =========================================
        # 6. 判断 Review 状态
        # =========================================
        if review.passed:
            review_status = "passed"

        elif auto_replan_round >= state["max_auto_replan_rounds"]:
            review_status = "exhausted"

        else:
            review_status = "replan_required"

        # =========================================
        # 7. 保存 Review Artifact
        # =========================================
        workspace = TaskWorkspace(state["task_id"])
        artifact_path = f"reviews/review_{review_round}.json"

        workspace.write_json(
            artifact_path,
            {
                "round": review_round,
                "auto_replan_round": auto_replan_round,
                "passed": review.passed,
                "status": review_status,
                "summary": review.summary,
                "issues": issues,
                "report_path": state["final_report_path"],
            },
        )

        # =========================================
        # 8. 更新 State
        # =========================================
        return {
            "review_round": review_round,
            "auto_replan_round": auto_replan_round,
            "review_status": review_status,
            "review_issues": issues,
            "review_artifacts": [artifact_path],
            "last_review_summary": review.summary,
            "current_step": f"review_{review_round}_{review_status}",
        }

    except Exception as e:
        # =========================================
        # 9. Reviewer 异常降级
        # =========================================
        return {
            "review_status": "exhausted",
            "warnings": [
                f"Reviewer执行失败：{type(e).__name__}: {e}"
            ],
            "current_step": "review_failed",
        }


# def route_after_review(
#     state: EnterpriseResearchState,
# ) -> Literal[
#     "pass",
#     "replan",
#     "exhausted",
# ]:
#     # =========================================
#     # 1. Review 通过
#     # =========================================
#     if state["review_status"] == "passed":
#         return "pass"

#     # =========================================
#     # 2. 需要重新规划
#     # =========================================
#     if state["review_status"] == "replan_required":
#         return "replan"

#     # =========================================
#     # 3. 达到 Review 上限
#     # =========================================
#     return "exhausted"


'''Evaluation 模式跳过人工审批'''
def route_after_review(
    state: EnterpriseResearchState,
) -> Literal["replan", "human", "finalize"]:
    # =========================================
    # 1. Reviewer 要求自动补充研究
    # =========================================
    if state["review_status"] == "replan_required":
        return "replan"

    # =========================================
    # 2. Evaluation 模式直接结束
    # =========================================
    if state.get("evaluation_mode", False):
        return "finalize"

    # =========================================
    # 3. 正常模式进入 HITL
    # =========================================
    return "human"


def _build_replan_context(state: EnterpriseResearchState) -> str:
    # =========================================
    # 1. 整理 Todo
    # =========================================
    todos = [
        {
            "id": todo["id"],
            "title": todo["title"],
            "description": todo["description"],
            "status": todo["status"],
            "assigned_agent": todo["assigned_agent"],
        }
        for todo in state["todos"]
    ]

    # =========================================
    # 2. 返回 Replan Context
    # =========================================
    return f"""
用户原始需求：
{state["user_query"]}

研究目标：
{state["plan_goal"]}

当前 Todo：
{json.dumps(todos, ensure_ascii=False)}

Reviewer Summary：
{state["last_review_summary"]}

Reviewer Issues：
{json.dumps(state["review_issues"], ensure_ascii=False)}
"""


def replan_node(state: EnterpriseResearchState) -> dict:
    try:
        # =========================================
        # 1. 构建 Replan Context
        # =========================================
        context = _build_replan_context(state)

        # =========================================
        # 2. 生成 Replan Decision
        # =========================================
        decision = generate_replan(context)

        if not decision.retry_todo_ids and not decision.new_tasks:
            raise ValueError("Replanner没有生成任何修复任务")

        # =========================================
        # 3. 重置需要 Retry 的失败 Todo
        # =========================================
        updated_todos = []

        for todo in state["todos"]:
            if (
                todo["id"] in decision.retry_todo_ids
                and todo["status"] == "failed"
            ):
                updated_todos.append({
                    **todo,
                    "status": "pending",
                    "assigned_agent": None,
                    "assignment_reason": None,
                    "artifact_path": None,
                    "source_artifact_path": None,
                    "knowledge_artifact_path": None,
                })
            else:
                updated_todos.append(todo)

        # =========================================
        # 4. 计算下一个 Todo ID
        # =========================================
        max_id = max(
            (int(todo["id"][1:]) for todo in updated_todos),
            default=0,
        )

        # =========================================
        # 5. 添加补充 Todo
        # =========================================
        new_todo_ids = []

        for index, task in enumerate(decision.new_tasks, start=1):
            todo_id = f"T{max_id + index:02d}"
            new_todo_ids.append(todo_id)

            updated_todos.append({
                "id": todo_id,
                "title": task.title,
                "description": task.description,
                "status": "pending",
                "assigned_agent": None,
                "assignment_reason": None,
                "artifact_path": None,
                "source_artifact_path": None,
                "knowledge_artifact_path": None,
            })

        # =========================================
        # 6. 保存 Replan Artifact
        # =========================================
        workspace = TaskWorkspace(state["task_id"])
        artifact_path = f"reviews/replan_{state['review_round']}.json"

        workspace.write_json(artifact_path, {
            "round": state["review_round"],
            "reason": decision.reason,
            "retry_todo_ids": decision.retry_todo_ids,
            "new_todo_ids": new_todo_ids,
            "new_tasks": [
                task.model_dump()
                for task in decision.new_tasks
            ],
        })

        # =========================================
        # 7. 更新 State
        # =========================================
        return {
            "todos": updated_todos,
            "current_todo_id": None,
            "current_agent": None,
            "review_status": "not_started",
            "replan_artifacts": [artifact_path],
            "current_step": f"replan_{state['review_round']}",
        }

    except Exception as e:
        # =========================================
        # 8. Replan 失败时结束修复循环
        # =========================================
        return {
            "review_status": "exhausted",
            "warnings": [
                f"Replan失败：{type(e).__name__}: {e}"
            ],
            "current_step": "replan_failed",
        }


def route_after_replan(
    state: EnterpriseResearchState,
) -> Literal[
    "continue",
    "stop",
]:
    # =========================================
    # 1. Replan 失败
    # =========================================
    if state["review_status"] == "exhausted":
        return "stop"

    # =========================================
    # 2. 继续执行补充任务
    # =========================================
    return "continue"


def route_after_synthesize(
    state: EnterpriseResearchState,
) -> Literal["review", "finalize"]:
    # =========================================
    # 1. 检查报告是否生成失败
    # =========================================
    if state["current_step"] == "synthesize_rejected":
        return "finalize"

    # =========================================
    # 2. 正常进入 Reviewer
    # =========================================
    return "review"