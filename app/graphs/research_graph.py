from langgraph.graph import END, START, StateGraph

from app.nodes.planning_nodes import (
    create_plan_node,
    route_after_plan,
    route_after_select,
    select_next_todo_node,
)

from app.nodes.research_nodes import (
    execute_current_todo_node,
    finalize_task_node,
    initialize_task_node,
    initialize_workspace_node,
    synthesize_report_node,
)

from app.states.research_state import (
    EnterpriseResearchState,
)

from app.nodes.supervisor_nodes import assign_subagent_node

from app.nodes.review_nodes import (
    replan_node,
    review_report_node,
    route_after_replan,
    route_after_review,
    route_after_synthesize
)

from app.checkpoint.sqlite import get_checkpointer

from app.nodes.hitl_nodes import (
    apply_human_revision_node,
    human_review_node,
    prepare_human_review_node,
    route_after_human_review,
)

from app.nodes.memory_nodes import (
    load_long_term_memory_node,
    save_long_term_memory_node,
)


def build_research_graph():

    workflow = StateGraph(
        EnterpriseResearchState
    )


    # =========================
    # Nodes
    # =========================

    workflow.add_node(
        "initialize_task",
        initialize_task_node,
    )

    workflow.add_node(
        "initialize_workspace",
        initialize_workspace_node,
    )

    workflow.add_node(
        "load_long_term_memory",
        load_long_term_memory_node,
    )

    workflow.add_node(
        "save_long_term_memory",
        save_long_term_memory_node,
    )

    workflow.add_node(
        "create_plan",
        create_plan_node,
    )

    workflow.add_node(
        "select_next_todo",
        select_next_todo_node,
    )

    workflow.add_node(
        "assign_subagent",
        assign_subagent_node,
    )

    workflow.add_node(
        "execute_current_todo",
        execute_current_todo_node,
    )

    workflow.add_node(
        "synthesize_report",
        synthesize_report_node,
    )

    workflow.add_node(
        "review_report",
        review_report_node,
    )

    workflow.add_node(
    "prepare_human_review",
    prepare_human_review_node,
)

    workflow.add_node(
        "human_review",
        human_review_node,
    )

    workflow.add_node(
        "apply_human_revision",
        apply_human_revision_node,
    )

    workflow.add_node(
        "replan",
        replan_node,
    )

    workflow.add_node(
        "finalize_task",
        finalize_task_node,
    )


    # =========================
    # Start
    # =========================

    workflow.add_edge(
        START,
        "initialize_task",
    )

    workflow.add_edge(
        "initialize_task",
        "initialize_workspace",
    )

    # =========================================
    # Long-Term Memory
    # =========================================
    workflow.add_edge(
        "initialize_workspace",
        "load_long_term_memory",
    )

    workflow.add_edge(
        "load_long_term_memory",
        "create_plan",
    )


    # =========================
    # Planner Router
    # =========================

    workflow.add_conditional_edges(
        "create_plan",

        route_after_plan,

        {
            "continue": "select_next_todo",

            "failed": "finalize_task",
        },
    )


    # =========================
    # Todo Router
    # =========================

    workflow.add_conditional_edges(
        "select_next_todo",
        route_after_select,
        {
            "execute": "assign_subagent",
            "done": "synthesize_report",
        },
    )

    workflow.add_edge(
        "assign_subagent",
        "execute_current_todo",
    )


    # =========================
    # Todo Loop
    # =========================

    workflow.add_edge(
        "execute_current_todo",
        "select_next_todo",
    )

    # =========================================
    # Review
    # =========================================
    workflow.add_conditional_edges(
        "synthesize_report",
        route_after_synthesize,
        {
            "review": "review_report",
            "finalize": "finalize_task",
        },
    )

    # =========================================
    # Reviewer Routing
    # =========================================
    # workflow.add_conditional_edges(
    #     "review_report",
    #     route_after_review,
    #     {
    #         "pass": "prepare_human_review",
    #         "replan": "replan",
    #         "exhausted": "prepare_human_review",
    #     },
    # )

    '''Evaluation 模式'''
    workflow.add_conditional_edges(
        "review_report",
        route_after_review,
        {
            "replan": "replan",
            "human": "prepare_human_review",
            "finalize": "finalize_task",
        },
    )

    # =========================================
    # Human Review
    # =========================================
    workflow.add_edge(
        "prepare_human_review",
        "human_review",
    )

    workflow.add_conditional_edges(
        "human_review",
        route_after_human_review,
        {
            "approve": "save_long_term_memory",
            "revise": "apply_human_revision",
            "reject": "finalize_task",
        },
    )

    workflow.add_edge(
        "save_long_term_memory",
        "finalize_task",
    )

    # =========================================
    # Human Revision
    # =========================================
    workflow.add_edge(
        "apply_human_revision",
        "select_next_todo",
    )

    # =========================================
    # Replan
    # =========================================
    workflow.add_conditional_edges(
        "replan",
        route_after_replan,
        {
            "continue": "select_next_todo",
            "stop": "finalize_task",
        },
    )

    workflow.add_edge(
        "finalize_task",
        END,
    )


    # =========================================
    # 编译持久化 Graph
    # =========================================
    return workflow.compile(
        checkpointer=get_checkpointer()
    )