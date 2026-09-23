from dotenv import load_dotenv

load_dotenv()

from app.graphs.research_graph import (
    build_research_graph,
)

from app.states.research_state import (
    create_initial_state,
)
from app.harness.research_harness import HARNESS_LIMITS
from langgraph.types import Command


def print_todos(state):
    # =========================================
    # 1. 获取 Todo List
    # =========================================
    todos = state.get("todos", [])

    if not todos:
        return

    # =========================================
    # 2. 定义状态符号
    # =========================================
    status_map = {
        "pending": "[ ]",
        "in_progress": "[>]",
        "completed": "[√]",
        "failed": "[x]",
    }

    # =========================================
    # 3. 输出 Todo
    # =========================================
    print("\nTodo List:")

    for todo in todos:
        symbol = status_map.get(todo["status"], "[?]")
        agent = todo.get("assigned_agent") or "-"
        artifact = todo.get("artifact_path") or "-"

        print(
            f"{symbol} {todo['id']} "
            f"[{agent}] "
            f"{todo['title']} "
            f"| Artifact: {artifact}"
        )


def print_review(state):
    # =========================================
    # 1. 判断是否进入 Review 阶段
    # =========================================
    current_step = state.get("current_step", "")

    if not current_step.startswith("review_"):
        return

    # =========================================
    # 2. 输出 Review 基本信息
    # =========================================
    print("\n" + "=" * 60)
    print("Reviewer Result")
    print("=" * 60)

    print(f"Review Round：{state.get('review_round', 0)}")
    print(f"Review Status：{state.get('review_status')}")

    # =========================================
    # 3. 输出 Reviewer 总结
    # =========================================
    summary = state.get("last_review_summary")

    if summary:
        print(f"\nReviewer Summary：\n{summary}")

    # =========================================
    # 4. 输出 Review Issues
    # =========================================
    issues = state.get("review_issues", [])

    if not issues:
        print("\nReview Issues：无")
        return

    print("\nReview Issues：")

    for issue in issues:
        print(
            f"\n[{issue['priority'].upper()}] "
            f"{issue['issue_id']} "
            f"({issue['category']})"
        )

        print(f"问题：{issue['description']}")
        print(f"建议：{issue['suggested_action']}")

        todo_ids = issue.get("related_todo_ids", [])

        if todo_ids:
            print(f"相关 Todo：{', '.join(todo_ids)}")


def print_replan(state):
    # =========================================
    # 1. 判断是否进入 Replan 阶段
    # =========================================
    current_step = state.get("current_step", "")

    if not current_step.startswith("replan_"):
        return

    # =========================================
    # 2. 输出 Replan 信息
    # =========================================
    print("\n" + "=" * 60)
    print("Replan Triggered")
    print("=" * 60)

    print(f"Review Round：{state.get('review_round')}")
    print("系统将根据 Reviewer 反馈继续执行补充研究。")

    # =========================================
    # 3. 输出最新 Todo
    # =========================================
    print_todos(state)


def print_harness_info():
    # =========================================
    # 1. 输出 Harness 标题
    # =========================================
    print("\n" + "=" * 60)
    print("Agent Harness")
    print("=" * 60)

    # =========================================
    # 2. 输出启用的 Middleware
    # =========================================
    middlewares = [
        "ModelRetryMiddleware",
        "ToolRetryMiddleware",
        "ToolCallLimitMiddleware",
        "ModelCallLimitMiddleware",
        "ContextEditingMiddleware",
        "SummarizationMiddleware",
    ]

    print("Enabled Middleware:")

    for name in middlewares:
        print(f"  - {name}")

    # =========================================
    # 3. 输出各 Subagent 调用预算
    # =========================================
    print("\nAgent Budgets:")

    for agent, limits in HARNESS_LIMITS.items():
        print(
            f"  {agent:<8} "
            f"tool={limits['tool_calls']}, "
            f"model={limits['model_calls']}"
        )


def ask_human_decision(interrupt_data):
    # =========================================
    # 1. 输出审批信息
    # =========================================
    print("\n" + "=" * 60)
    print("Human Review Required")
    print("=" * 60)

    print(f"报告：{interrupt_data['report_path']}")
    print(f"Reviewer：{interrupt_data['review_summary']}")

    # =========================================
    # 2. 获取人工决策
    # =========================================
    action_map = {
        "1": "approve",
        "2": "revise",
        "3": "reject",
    }

    while True:
        print("\n可选操作：")
        print("1. approve  批准报告")
        print("2. revise   要求修改")
        print("3. reject   拒绝报告")

        value = input("\n请输入操作：").strip().lower()
        action = action_map.get(value, value)

        if action in {"approve", "revise", "reject"}:
            break

        print("输入无效，请重新输入。")

    # =========================================
    # 3. 获取人工反馈
    # =========================================
    feedback = ""

    if action == "revise":
        while not feedback:
            feedback = input("请输入修改要求：").strip()

    elif action == "reject":
        feedback = input("请输入拒绝原因（可选）：").strip()

    # =========================================
    # 4. 返回 Resume 数据
    # =========================================
    return {
        "action": action,
        "feedback": feedback,
    }


def print_graph_state(state, previous_step):
    # =========================================
    # 1. 获取当前执行阶段
    # =========================================
    current_step = state.get("current_step", "")

    if current_step == previous_step:
        return previous_step

    # =========================================
    # 2. 输出当前状态
    # =========================================
    print(
        f"\n[{state.get('status')}] "
        f"{current_step}"
    )

    print_todos(state)

    # =========================================
    # 3. 输出 Harness Budget
    # =========================================
    if current_step.startswith("assigned_"):
        agent_type = state.get("current_agent")

        if agent_type in HARNESS_LIMITS:
            limits = HARNESS_LIMITS[agent_type]

            print(
                f"\nHarness Budget -> "
                f"Agent: {agent_type}, "
                f"Tool Calls: {limits['tool_calls']}, "
                f"Model Calls: {limits['model_calls']}"
            )

    # =========================================
    # 4. 输出 Reviewer / Replan
    # =========================================
    print_review(state)
    print_replan(state)

    # =========================================
    # 5. 输出 Long-Term Memory
    # =========================================
    print_memory(state)

    # =========================================
    # 6. 返回最新阶段
    # =========================================
    return current_step


def print_memory(state):
    # =========================================
    # 1. 获取当前步骤
    # =========================================
    step = state.get("current_step", "")

    # =========================================
    # 2. 输出读取到的长期记忆
    # =========================================
    if step == "memory_loaded":
        memory_ids = state.get("retrieved_memory_ids", [])

        print("\nLong-Term Memory:")
        print(
            "Retrieved Episodes: "
            + (", ".join(memory_ids) if memory_ids else "None")
        )

    # =========================================
    # 3. 输出保存的长期记忆
    # =========================================
    elif step == "memory_saved":
        memory_ids = state.get("stored_memory_ids", [])

        print("\nLong-Term Memory:")
        print(
            "Saved Episodes: "
            + (", ".join(memory_ids) if memory_ids else "None")
        )


def main():
    # =========================================
    # 1. 创建 Enterprise Research Graph
    # =========================================
    graph = build_research_graph()

    print("=" * 60)
    print("Enterprise Research Agent")
    print("Stage 10: Human-in-the-loop")
    print("=" * 60)

    print_harness_info()

    # =========================================
    # 2. 创建研究任务
    # =========================================
    query = input("\n请输入企业研究任务：").strip()

    initial_state = create_initial_state(
        user_query=query
    )

    task_id = initial_state["task_id"]

    print(f"\n任务ID：{task_id}")

    # =========================================
    # 3. 配置 Checkpoint Thread
    # =========================================
    config = {
        "configurable": {
            "thread_id": task_id
        },
        "recursion_limit": 100,
    }

    # =========================================
    # 4. 准备首次 Graph 输入
    # =========================================
    graph_input = initial_state

    final_state = None
    previous_step = None

    # =========================================
    # 5. 持续运行 Graph
    # =========================================
    while True:

        for state in graph.stream(
            graph_input,
            config=config,
            stream_mode="values",
        ):
            final_state = state

            previous_step = print_graph_state(
                state,
                previous_step,
            )

        # =========================================
        # 6. 读取最新 Checkpoint
        # =========================================
        snapshot = graph.get_state(config)

        final_state = snapshot.values

        # =========================================
        # 7. 检查是否存在 Human Interrupt
        # =========================================
        if not snapshot.interrupts:
            break

        interrupt_data = (
            snapshot.interrupts[0].value
        )

        # =========================================
        # 8. 获取人工审批结果
        # =========================================
        decision = ask_human_decision(
            interrupt_data
        )

        # =========================================
        # 9. 使用 Command 恢复 Graph
        # =========================================
        graph_input = Command(
            resume=decision
        )

    # =========================================
    # 10. 输出最终任务结果
    # =========================================
    if final_state is None:
        return

    print("\n" + "=" * 60)
    print(f"最终状态：{final_state['status']}")

    print_todos(final_state)

    # =========================================
    # 11. 输出错误信息
    # =========================================
    if final_state.get("errors"):
        print("\n错误记录：")

        for error in final_state["errors"]:
            print(error)

    # =========================================
    # 12. 输出最终报告
    # =========================================
    if final_state.get("final_answer"):
        print("\n最终研究结果：\n")
        print(final_state["final_answer"])

    print(
        f"\nWorkspace："
        f"{final_state.get('workspace_path')}"
    )

    print(
        f"最终报告："
        f"{final_state.get('final_report_path')}"
    )

    # =========================================
    # 13. 输出 Research Artifacts
    # =========================================
    print("\nResearch Artifacts:")

    for artifact in final_state.get(
        "research_artifacts",
        [],
    ):
        print(f"  {artifact}")


if __name__ == "__main__":
    main()