from langchain.agents import create_agent

from app.core.model import get_model
from app.prompts.subagent_prompts import (
    COMPANY_PROMPT,
    FINANCE_PROMPT,
    GENERAL_PROMPT,
    MARKET_PROMPT,
    RISK_PROMPT,
)
from app.schemas.subagent_route import AgentType
from app.tools.calculator import calculator
from app.tools.current_date import get_current_date
from app.tools.knowledge_tools import build_knowledge_tools
from app.tools.research_tools import build_research_tools

from app.harness.research_harness import build_research_harness


def _select_search_tools(task_id: str, todo_id: str, names: list[str]):
    # =========================================
    # 1. 获取全部 Research Tools
    # =========================================
    tools = build_research_tools(task_id, todo_id)
    tool_map = {tool.name: tool for tool in tools}

    # =========================================
    # 2. 根据权限选择工具
    # =========================================
    return [tool_map[name] for name in names if name in tool_map]


def build_subagent(
    agent_type: AgentType,
    task_id: str,
    todo_id: str,
    use_harness: bool = True,
):
    # =========================================
    # 1. 定义 Subagent 配置
    # =========================================
    configs = {
        "company": {
            "prompt": COMPANY_PROMPT,
            "search": ["general_search", "news_search"],
            "knowledge": False,
        },
        "market": {
            "prompt": MARKET_PROMPT,
            "search": ["general_search", "news_search"],
            "knowledge": False,
        },
        "finance": {
            "prompt": FINANCE_PROMPT,
            "search": ["finance_search", "general_search"],
            "knowledge": False,
        },
        "risk": {
            "prompt": RISK_PROMPT,
            "search": ["general_search", "news_search", "finance_search"],
            "knowledge": True,
        },
        "general": {
            "prompt": GENERAL_PROMPT,
            "search": ["general_search", "news_search", "finance_search"],
            "knowledge": True,
        },
    }

    # =========================================
    # 2. 获取 Agent 配置
    # =========================================
    config = configs[agent_type]

    # =========================================
    # 3. 创建 Agent Tools
    # =========================================
    tools = _select_search_tools(task_id, todo_id, config["search"])
    tools += [calculator, get_current_date]

    if config["knowledge"]:
        tools += build_knowledge_tools(task_id, todo_id)

    # =========================================
    # 4. 创建 MiMo
    # =========================================
    model = get_model(max_retries=0 if use_harness else 2)

    # =========================================
    # 5. 创建 Agent Harness
    # =========================================
    middleware = (
        build_research_harness(agent_type, model)
        if use_harness
        else []
    )

    # =========================================
    # 6. 创建专业 Subagent
    # =========================================
    return create_agent(
        model=model,
        tools=tools,
        system_prompt=config["prompt"],
        middleware=middleware,
        name=f"{agent_type}_research_agent",
    )