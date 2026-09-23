from typing import Literal

from langchain.tools import tool

from app.services.search_service import (
    ResearchSearchService,
)
from app.services.source_store import (
    SourceStore,
)


def build_research_tools(
    task_id: str,
    todo_id: str,
):
    """
    为当前 Task + Todo 创建具有上下文的
    Research Tools。
    """

    search_service = (
        ResearchSearchService()
    )

    source_store = SourceStore(
        task_id=task_id,
        todo_id=todo_id,
    )


    def run_search(
        query: str,
        topic: str,
        time_range: str | None,
        max_results: int,
    ) -> str:
        """
        内部统一搜索函数。
        """

        sources = (
            search_service.search(
                query=query,
                topic=topic,
                time_range=time_range,
                max_results=max_results,
            )
        )


        if not sources:
            return (
                "本次搜索未找到可用结果。"
            )


        sources = (
            source_store.save_sources(
                sources
            )
        )


        output = [
            (
                f"搜索关键词：{query}\n"
                f"共返回 {len(sources)} "
                f"个来源："
            )
        ]


        for source in sources:

            output.append(
                f"""
[{source.source_id}]
标题：{source.title}
URL：{source.url}
相关度：{source.score}
摘要：{source.snippet}
""".strip()
            )


        return "\n\n".join(
            output
        )


    @tool
    def general_search(
        query: str,
        max_results: int = 5,
    ) -> str:
        """
        搜索企业、产品、技术、市场、竞争对手等一般信息。

        适用于企业背景、产品信息、行业信息、
        技术信息、竞争格局等研究任务。

        参数:
            query: 搜索关键词，应尽量具体。
            max_results: 返回结果数量，建议3到5条。
        """

        return run_search(
            query=query,
            topic="general",
            time_range=None,
            max_results=max_results,
        )


    @tool
    def news_search(
        query: str,
        time_range: Literal[
            "day",
            "week",
            "month",
            "year",
        ] = "year",
        max_results: int = 5,
    ) -> str:
        """
        搜索新闻和近期企业动态。

        适用于公司近期事件、产品发布、
        战略合作、收购、监管事件等。

        参数:
            query: 新闻搜索关键词。
            time_range: 搜索时间范围。
            max_results: 返回结果数量。
        """

        return run_search(
            query=query,
            topic="news",
            time_range=time_range,
            max_results=max_results,
        )


    @tool
    def finance_search(
        query: str,
        max_results: int = 5,
    ) -> str:
        """
        搜索企业财务、收入、业绩、财报和市场相关信息。

        涉及企业收入、利润、季度业绩、
        财报等问题时优先使用。
        """

        return run_search(
            query=query,
            topic="finance",
            time_range=None,
            max_results=max_results,
        )


    return [
        general_search,
        news_search,
        finance_search,
    ]