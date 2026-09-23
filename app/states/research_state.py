import operator

from typing import Annotated, Literal, TypedDict
from uuid import uuid4

from langchain.messages import AnyMessage
from langgraph.graph import add_messages

from app.schemas.subagent_route import AgentType


ResearchStatus = Literal[
    "created",
    "running",
    "waiting_human",
    "completed",
    "completed_with_warnings",
    "rejected",
    "failed",
]


TodoStatus = Literal[
    "pending",
    "in_progress",
    "completed",
    "failed",
]

ReviewStatus = Literal[
    "not_started",
    "passed",
    "replan_required",
    "exhausted",
]

HumanReviewStatus = Literal[
    "not_requested",
    "waiting",
    "approved",
    "revision_requested",
    "rejected",
]


class TodoItem(TypedDict):
    id: str
    title: str
    description: str
    status: TodoStatus

    assigned_agent: AgentType | None
    assignment_reason: str | None

    artifact_path: str | None
    source_artifact_path: str | None
    knowledge_artifact_path: str | None


class EnterpriseResearchState(TypedDict):

    # Task
    task_id: str
    user_query: str
    status: ResearchStatus
    current_step: str

    # Workspace
    workspace_path: str | None

    research_artifacts: Annotated[
        list[str],
        operator.add,
    ]

    final_report_path: str | None

    # Planner
    plan_goal: str | None

    todos: list[TodoItem]

    current_todo_id: str | None

    # Research
    source_artifacts: Annotated[
        list[str],
        operator.add,
    ]

    errors: Annotated[
        list[str],
        operator.add,
    ]

    # Messages
    messages: Annotated[
        list[AnyMessage],
        add_messages,
    ]

    # Final
    final_answer: str | None

    knowledge_artifacts: Annotated[
        list[str],
        operator.add,
    ]

    current_agent: AgentType | None

    # Review
    review_round: int
    auto_replan_round: int
    max_auto_replan_rounds: int
    review_status: ReviewStatus

    review_issues: list[dict]

    review_artifacts: Annotated[
        list[str],
        operator.add,
    ]

    replan_artifacts: Annotated[
        list[str],
        operator.add,
    ]

    last_review_summary: str | None

    # Human Review
    human_review_status: HumanReviewStatus

    human_review_round: int

    human_feedback: str | None

    human_review_artifacts: Annotated[
        list[str],
        operator.add,
    ]

    # Long-Term Memory
    user_id: str

    memory_context: str

    retrieved_memory_ids: list[str]

    stored_memory_ids: Annotated[
        list[str],
        operator.add,
    ]

    # Evaluation
    evaluation_mode: bool

    use_harness: bool


def create_initial_state(
    user_query: str,
    user_id: str = "local_user",
    evaluation_mode: bool = False,
    use_harness: bool = True,
) -> EnterpriseResearchState:

    return {
        "task_id": str(uuid4()),

        "user_query": user_query,

        "status": "created",

        "current_step": "waiting",

        "workspace_path": None,

        "research_artifacts": [],

        "final_report_path": None,

        "plan_goal": None,

        "todos": [],

        "current_todo_id": None,

        "sources": [],

        "errors": [],

        "messages": [],

        "final_answer": None,

        "knowledge_artifacts": [],

        "current_agent": None,

        "review_round": 0,
        "auto_replan_round": 0,
        "max_auto_replan_rounds": 2,
        "review_status": "not_started",

        "review_issues": [],

        "review_artifacts": [],
        "replan_artifacts": [],

        "last_review_summary": None,

        "human_review_status": "not_requested",
        "human_review_round": 0,
        "human_feedback": None,
        "human_review_artifacts": [],

        "user_id": user_id,

        "memory_context": "",
        "retrieved_memory_ids": [],
        "stored_memory_ids": [],

        "evaluation_mode": evaluation_mode,

        "use_harness": use_harness
    }