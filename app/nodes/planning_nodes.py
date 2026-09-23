from typing import Literal

from app.states.research_state import (
    EnterpriseResearchState,
    TodoItem,
)

from app.workspace.manager import TaskWorkspace

from app.agents.planner_agent import generate_research_plan

def create_plan_node(
    state: EnterpriseResearchState,
) -> dict:
    """
    根据用户任务生成研究计划。
    """

    try:

        # =========================================
        # 1. 生成带长期记忆的研究计划
        # =========================================
        plan = generate_research_plan(
            user_query=state["user_query"],
            memory_context=state["memory_context"],
        )


        if plan is None:

            raise ValueError(
                "Planner 未返回结构化研究计划"
            )


        todos: list[TodoItem] = []


        for index, task in enumerate(
            plan.tasks,
            start=1,
        ):

            todos.append(
                {
                    "id": f"T{index:02d}",

                    "title": task.title,

                    "description": task.description,

                    "status": "pending",

                    "artifact_path": None,
                }
            )


        workspace = TaskWorkspace(
            task_id=state["task_id"]
        )


        workspace.write_json(
            "plan.json",
            {
                "goal": plan.goal,

                "tasks": [
                    {
                        "id": todo["id"],

                        "title": todo["title"],

                        "description": (
                            todo["description"]
                        ),
                    }
                    for todo in todos
                ],
            },
        )


        return {
            "plan_goal": plan.goal,

            "todos": todos,

            "current_step": "planning",
        }


    except Exception as e:

        return {
            "status": "failed",

            "current_step": "planning_failed",

            "errors": [
                (
                    "Planner失败: "
                    f"{type(e).__name__}: {e}"
                )
            ],
        }

def select_next_todo_node(
    state: EnterpriseResearchState,
) -> dict:
    """
    从 Todo List 中选择下一个 pending 任务。
    """

    todos = state["todos"]

    next_todo = None

    for todo in todos:

        if todo["status"] == "pending":
            next_todo = todo
            break


    if next_todo is None:

        return {
            "current_todo_id": None,

            "current_step": "plan_completed",
        }


    updated_todos = []

    for todo in todos:

        if todo["id"] == next_todo["id"]:

            updated_todos.append(
                {
                    **todo,
                    "status": "in_progress",
                }
            )

        else:

            updated_todos.append(todo)


    return {
        "todos": updated_todos,

        "current_todo_id": next_todo["id"],

        "current_step": (
            f"executing_{next_todo['id']}"
        ),
    }


def route_after_plan(
    state: EnterpriseResearchState,
) -> Literal[
    "continue",
    "failed",
]:

    if state["status"] == "failed":
        return "failed"

    return "continue"


def route_after_select(
    state: EnterpriseResearchState,
) -> Literal[
    "execute",
    "done",
]:

    if state["current_todo_id"] is None:
        return "done"

    return "execute"