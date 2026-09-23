import re
import time

from app.graphs.research_graph import build_research_graph
from app.states.research_state import create_initial_state
from app.workspace.manager import TaskWorkspace


SOURCE_PATTERN = re.compile(r"T\d{2}-S\d{1,3}")
KNOWLEDGE_PATTERN = re.compile(r"KB-[A-Z0-9-]+")


def _collect_ids(data, field_name: str) -> set[str]:
    # =========================================
    # 1. 递归收集 JSON 中指定字段
    # =========================================
    results = set()

    if isinstance(data, dict):
        value = data.get(field_name)

        if isinstance(value, str):
            results.add(value)

        for child in data.values():
            results.update(
                _collect_ids(child, field_name)
            )

    elif isinstance(data, list):
        for child in data:
            results.update(
                _collect_ids(child, field_name)
            )

    return results


def _load_available_ids(
    state,
    workspace: TaskWorkspace,
) -> tuple[list[str], list[str]]:
    # =========================================
    # 1. 收集 External Source IDs
    # =========================================
    source_ids = set()

    for path in set(state.get("source_artifacts", [])):
        if workspace.exists(path):
            data = workspace.read_json(path)
            source_ids.update(
                _collect_ids(data, "source_id")
            )

    # =========================================
    # 2. 收集 Knowledge Evidence IDs
    # =========================================
    knowledge_ids = set()

    for path in set(state.get("knowledge_artifacts", [])):
        if workspace.exists(path):
            data = workspace.read_json(path)
            knowledge_ids.update(
                _collect_ids(data, "evidence_id")
            )

    return sorted(source_ids), sorted(knowledge_ids)


def run_research_target(inputs: dict) -> dict:
    # =========================================
    # 1. 创建 Evaluation State
    # =========================================
    initial_state = create_initial_state(
        user_query=inputs["query"],
        user_id="benchmark_user",
        evaluation_mode=True,
        use_harness=inputs.get("use_harness", True),
    )

    task_id = initial_state["task_id"]

    # =========================================
    # 2. 创建 Graph
    # =========================================
    graph = build_research_graph()

    config = {
        "configurable": {
            "thread_id": task_id,
        },
        "recursion_limit": 100,
        "tags": [
            "stage12",
            "evaluation",
        ],
        "metadata": {
            "evaluation_mode": True,
            "task_id": task_id,
        },
    }

    # =========================================
    # 3. 执行完整 Agent
    # =========================================
    start_time = time.perf_counter()

    final_state = graph.invoke(
        initial_state,
        config=config,
    )

    latency = time.perf_counter() - start_time

    # =========================================
    # 4. 获取最终报告
    # =========================================
    report = final_state.get("final_answer") or ""

    # =========================================
    # 5. 提取实际 Agent Trajectory
    # =========================================
    agents_used = []

    for todo in final_state.get("todos", []):
        agent = todo.get("assigned_agent")

        if agent and agent not in agents_used:
            agents_used.append(agent)

    # =========================================
    # 6. 收集真实 Evidence IDs
    # =========================================
    workspace = TaskWorkspace(task_id)

    source_ids, knowledge_ids = _load_available_ids(
        final_state,
        workspace,
    )

    # =========================================
    # 7. 提取报告实际引用
    # =========================================
    cited_source_ids = sorted(
        set(SOURCE_PATTERN.findall(report))
    )

    cited_knowledge_ids = sorted(
        set(KNOWLEDGE_PATTERN.findall(report))
    )

    # =========================================
    # 8. 返回 LangSmith Evaluation Output
    # =========================================
    return {
    "task_id": task_id,
    "status": final_state["status"],
    "review_status": final_state["review_status"],
    "current_step": final_state.get("current_step"),
    "report": report,
    "todos": final_state.get("todos", []),
    "agents_used": agents_used,
    "errors": final_state.get("errors", []),
    "warnings": final_state.get("warnings", []),
    "source_ids": source_ids,
    "knowledge_ids": knowledge_ids,
    "cited_source_ids": cited_source_ids,
    "cited_knowledge_ids": cited_knowledge_ids,
    "latency_seconds": round(latency, 2),
    "use_harness": initial_state["use_harness"],
}