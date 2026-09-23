from app.agents.subagents import build_subagent
from app.states.research_state import EnterpriseResearchState

from langchain.messages import HumanMessage, SystemMessage

from app.core.model import get_model

from app.workspace.manager import TaskWorkspace

from datetime import datetime, timezone

from app.core.output_validation import is_model_rejection


def initialize_task_node(
    state: EnterpriseResearchState,
) -> dict:
    """
    初始化研究任务。
    """

    return {
        "status": "running",
        "current_step": "initialize",
    }

###################################
###         第二阶段，工作流
###################################


# def baseline_research_node(
#     state: EnterpriseResearchState,
# ) -> dict:
#     """
#     调用阶段1实现的 Baseline Agent 执行研究任务。
#     """

#     try:
#         agent = build_baseline_agent()

#         result = agent.invoke(
#             {
#                 "messages": [
#                     {
#                         "role": "user",
#                         "content": state["user_query"],
#                     }
#                 ]
#             }
#         )

#         final_message = result["messages"][-1]

#         final_text = str(final_message.content)

#         return {
#             "current_step": "baseline_research",

#             "messages": result["messages"],

#             "research_results": [
#                 final_text
#             ],

#             "final_answer": final_text,
#         }

#     except Exception as e:

#         return {
#             "current_step": "baseline_research",

#             "errors": [
#                 f"{type(e).__name__}: {e}"
#             ],
#         }


###################################
###         第三阶段，planner
###################################


def execute_current_todo_node(state: EnterpriseResearchState) -> dict:
    # =========================================
    # 1. 获取当前 Todo
    # =========================================
    todo_id = state["current_todo_id"]
    current_todo = next(
        (todo for todo in state["todos"] if todo["id"] == todo_id),
        None,
    )

    if current_todo is None:
        return {
            "errors": [f"找不到当前任务：{todo_id}"],
            "current_step": "todo_error",
        }

    try:
        # =========================================
        # 2. 创建当前专业 Subagent
        # =========================================
        agent_type = current_todo["assigned_agent"] or "general"

        agent = build_subagent(
            agent_type=agent_type,
            task_id=state["task_id"],
            todo_id=todo_id,
            use_harness=state.get("use_harness", True),
        )

        # =========================================
        # 3. 构建独立 Subagent Context
        # =========================================
        task_prompt = f"""
原始研究目标：
{state["user_query"]}

当前只完成这个 Todo：

任务编号：{todo_id}
标题：{current_todo["title"]}
要求：{current_todo["description"]}

你是 {agent_type} Subagent。

只完成当前任务，不生成完整研究报告。
"""

        # =========================================
        # 4. 执行 Subagent
        # =========================================
        result = agent.invoke({
            "messages": [{"role": "user", "content": task_prompt}]
        })

        final_message = result["messages"][-1]
        result_text = (
            final_message.content
            if isinstance(final_message.content, str)
            else str(final_message.content)
        )

        # =========================================
        # 5. 检查 Evidence Artifact
        # =========================================
        workspace = TaskWorkspace(state["task_id"])

        source_path = f"sources/{todo_id}.json"
        knowledge_path = f"knowledge/{todo_id}.json"

        has_sources = workspace.exists(source_path)
        has_knowledge = workspace.exists(knowledge_path)

        # =========================================
        # 6. 构建 Research Artifact
        # =========================================
        artifact_path = f"research/{todo_id}.md"

        artifact_content = f"""# {current_todo["title"]}

## Task ID
{todo_id}

## Assigned Agent
{agent_type}

## Research Requirement
{current_todo["description"]}

## External Source Artifact
{source_path if has_sources else "无"}

## Internal Knowledge Artifact
{knowledge_path if has_knowledge else "无"}

## Research Result
{result_text}
"""

        # =========================================
        # 7. 保存 Research Artifact
        # =========================================
        workspace.write_text(artifact_path, artifact_content)

        # =========================================
        # 8. 更新 Todo
        # =========================================
        updated_todos = [
            {
                **todo,
                "status": "completed",
                "artifact_path": artifact_path,
                "source_artifact_path": source_path if has_sources else None,
                "knowledge_artifact_path": knowledge_path if has_knowledge else None,
            }
            if todo["id"] == todo_id else todo
            for todo in state["todos"]
        ]

        # =========================================
        # 9. 更新 State
        # =========================================
        update = {
            "todos": updated_todos,
            "current_todo_id": None,
            "current_agent": None,
            "research_artifacts": [artifact_path],
            "current_step": f"completed_{todo_id}",
        }

        if has_sources:
            update["source_artifacts"] = [source_path]

        if has_knowledge:
            update["knowledge_artifacts"] = [knowledge_path]

        return update

    except Exception as e:
        # =========================================
        # 10. 记录失败 Todo
        # =========================================
        error = f"{type(e).__name__}: {e}"

        updated_todos = [
            {**todo, "status": "failed"}
            if todo["id"] == todo_id else todo
            for todo in state["todos"]
        ]

        return {
            "todos": updated_todos,
            "current_todo_id": None,
            "current_agent": None,
            "errors": [f"{todo_id} 执行失败：{error}"],
            "current_step": f"failed_{todo_id}",
        }


def synthesize_report_node(
    state: EnterpriseResearchState,
) -> dict:
    """
    将所有已完成 Todo 的研究结果汇总。

    Todo
    ↓
    research/T01.md

    Todo
    ↓
    research/T02.md

    Todo
    ↓
    research/T03.md

        ↓

    Synthesizer

        ↓

    读取 T01.md
    读取 T02.md
    读取 T03.md

        ↓

    生成最终报告

        ↓

    final/report.md

    """
    try:

        workspace = TaskWorkspace(
            task_id=state["task_id"]
        )


        completed_results = []


        for todo in state["todos"]:

            if (
                todo["status"] == "completed"
                and todo["artifact_path"]
            ):

                content = workspace.read_text(
                    todo["artifact_path"]
                )

                completed_results.append(
                    content
                )


        if not completed_results:

            raise ValueError(
                "没有可用于生成报告的研究结果"
            )


        research_context = (
            "\n\n"
            "====================\n\n"
        ).join(
            completed_results
        )

        source_contexts = []


        for source_path in state[
            "source_artifacts"
        ]:

            if not workspace.exists(
                source_path
            ):
                continue


            source_data = (
                workspace.read_json(
                    source_path
                )
            )


            for source in source_data.get(
                "sources",
                [],
            ):

                source_contexts.append(
                    f"""
        [{source["source_id"]}]
        标题：{source["title"]}
        URL：{source["url"]}
        摘要：{source["snippet"]}
        """.strip()
                )


        source_context = "\n\n".join(
            source_contexts
        )

        knowledge_contexts = []


        for knowledge_path in state[
            "knowledge_artifacts"
        ]:

            if not workspace.exists(
                knowledge_path
            ):
                continue


            knowledge_data = (
                workspace.read_json(
                    knowledge_path
                )
            )


            for evidence in (
                knowledge_data.get(
                    "evidences",
                    [],
                )
            ):

                knowledge_contexts.append(
                    f"""
        [{evidence["evidence_id"]}]
        文档：{evidence["title"]}
        源文件：{evidence["source_file"]}
        内容：
        {evidence["content"]}
        """.strip()
                )


        knowledge_context = (
            "\n\n".join(
                knowledge_contexts
            )
        )


        system_prompt = """
你是一名企业研究报告整理助手。

你会收到：

1. 用户原始研究需求
2. 研究目标
3. 多个已经完成的研究 Artifact

请基于已有研究成果生成最终研究报告。

要求：

1. 完整覆盖用户的原始研究需求。
2. 不得虚构 Artifact 中不存在的信息。
3. 尽量保留原始研究成果中的来源 URL。
4. 合并重复内容。
5. 使用清晰结构组织报告。
6. 信息不足时明确指出。
"""


        user_prompt = f"""
用户原始需求：

{state["user_query"]}


研究目标：

{state["plan_goal"]}


Research Artifacts：

{research_context}


External Source Index：

{source_context}


Internal Knowledge Evidence：

{knowledge_context}


请生成最终企业研究报告。

要求：

1. 公开互联网事实使用对应 Source ID。

2. 企业内部知识使用对应 Knowledge Evidence ID。

3. 不得生成不存在的 Evidence ID。

4. 重要结论应尽量能够追溯到证据。

5. 如果内部知识库与公开信息分别描述不同层面的内容，
   应明确区分。

6. 信息不足时明确说明。
"""


        model = get_model()


        response = model.invoke(
            [
                SystemMessage(
                    content=system_prompt
                ),

                HumanMessage(
                    content=user_prompt
                ),
            ]
        )


        if isinstance(
            response.content,
            str,
        ):
            final_text = response.content

        else:

            final_text = str(
                response.content
            )

        # =========================================
        # 6. 检查模型是否拒绝生成报告
        # =========================================
        if is_model_rejection(final_text):
            rejection_path = (
                f"reviews/synthesis_rejection_"
                f"{state['review_round'] + 1}.txt"
            )

            workspace.write_text(
                rejection_path,
                final_text,
            )

            return {
                "warnings": [
                    "本轮报告生成被模型安全策略拒绝，"
                    "保留上一版有效报告。"
                ],
                "current_step": "synthesize_rejected",
            }

        # =========================================
        # 7. 保存有效 Report Artifact
        # =========================================
        report_version = state["review_round"] + 1
        final_report_path = f"final/report_v{report_version}.md"

        workspace.write_text(
            final_report_path,
            final_text,
        )

        return {
            "final_answer": final_text,
            "final_report_path": final_report_path,
            "current_step": f"synthesize_report_v{report_version}",
        }



    except Exception as e:

        return {
            "errors": [
                (
                    "最终汇总失败: "
                    f"{type(e).__name__}: {e}"
                )
            ],

            "current_step": (
                "synthesize_failed"
            ),
        }


def finalize_task_node(state: EnterpriseResearchState) -> dict:
    # =========================================
    # 1. 获取 Workspace
    # =========================================
    workspace = TaskWorkspace(state["task_id"])

    # =========================================
    # 2. 判断最终任务状态
    # =========================================
    if not state["final_report_path"]:
        final_status = "failed"

    elif state.get("evaluation_mode", False):
        final_status = (
            "completed"
            if state["review_status"] == "passed"
            else "completed_with_warnings"
        )

    elif state["human_review_status"] == "rejected":
        final_status = "rejected"

    elif state["human_review_status"] == "approved":
        final_status = (
            "completed"
            if state["review_status"] == "passed"
            else "completed_with_warnings"
        )

    else:
        final_status = "completed_with_warnings"

    # =========================================
    # 3. 发布最终报告
    # =========================================
    final_report_path = state["final_report_path"]

    if (
        final_status != "rejected"
        and final_report_path
        and workspace.exists(final_report_path)
    ):
        content = workspace.read_text(
            final_report_path
        )

        workspace.write_text(
            "final/report.md",
            content,
        )

        final_report_path = (
            "final/report.md"
        )

    # =========================================
    # 4. 更新 task.json
    # =========================================
    try:
        task_info = workspace.read_json("task.json")
    except Exception:
        task_info = {
            "task_id": state["task_id"],
            "user_query": state["user_query"],
        }

    task_info.update({
        "status": final_status,
        "review_status": state["review_status"],
        "review_rounds": state["review_round"],
        "final_report_path": final_report_path,
    })

    workspace.write_json("task.json", task_info)

    # =========================================
    # 5. 更新最终 State
    # =========================================
    return {
        "status": final_status,
        "final_report_path": final_report_path,
        "current_step": "finished",
    }


def initialize_workspace_node(
    state: EnterpriseResearchState,
) -> dict:
    """
    为当前 Research Task 创建独立 Workspace。
    """

    try:

        workspace = TaskWorkspace(
            task_id=state["task_id"]
        )

        workspace.create(
            user_query=state["user_query"]
        )

        return {
            "workspace_path": workspace.get_path(),

            "current_step": "workspace_initialized",
        }


    except Exception as e:

        return {
            "status": "failed",

            "current_step": "workspace_failed",

            "errors": [
                (
                    "Workspace初始化失败: "
                    f"{type(e).__name__}: {e}"
                )
            ],
        }