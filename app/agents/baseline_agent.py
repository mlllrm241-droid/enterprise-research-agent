from langchain.agents import create_agent

from app.core.model import get_model
from app.prompts.baseline_prompt import BASELINE_SYSTEM_PROMPT
from app.tools.calculator import calculator
from app.tools.current_date import get_current_date
from app.tools.search import web_search


def build_baseline_agent():
    model = get_model()

    tools = [
        web_search,
        calculator,
        get_current_date,
    ]

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=BASELINE_SYSTEM_PROMPT,
        name="enterprise_research_baseline",
    )

    return agent