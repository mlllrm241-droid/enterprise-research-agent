from langchain.agents import create_agent

from app.core.model import get_model
from app.prompts.research_prompt import (
    RESEARCH_SYSTEM_PROMPT,
)
from app.tools.calculator import (
    calculator,
)
from app.tools.current_date import (
    get_current_date,
)
from app.tools.research_tools import (
    build_research_tools,
)
from app.tools.knowledge_tools import (
    build_knowledge_tools,
)


def build_research_agent(
    task_id: str,
    todo_id: str,
):
    """
    创建当前 Todo 专属的 Research Agent。
    """

    model = get_model()


    research_tools = (
        build_research_tools(
            task_id=task_id,
            todo_id=todo_id,
        )
    )


    tools = [
        *research_tools,
        calculator,
        get_current_date,
    ]


    return create_agent(
        model=model,

        tools=tools,

        system_prompt=(
            RESEARCH_SYSTEM_PROMPT
        ),

        name=(
            "enterprise_research_agent"
        ),
    )

def build_research_agent(
    task_id: str,
    todo_id: str,
):

    model = get_model()


    research_tools = (
        build_research_tools(
            task_id=task_id,
            todo_id=todo_id,
        )
    )


    knowledge_tools = (
        build_knowledge_tools(
            task_id=task_id,
            todo_id=todo_id,
        )
    )


    tools = [
        *research_tools,

        *knowledge_tools,

        calculator,

        get_current_date,
    ]


    return create_agent(
        model=model,

        tools=tools,

        system_prompt=(
            RESEARCH_SYSTEM_PROMPT
        ),

        name=(
            "enterprise_research_agent"
        ),
    )