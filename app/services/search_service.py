import json

from datetime import (
    datetime,
    timezone,
)
from typing import Literal

from langchain_tavily import TavilySearch

from app.schemas.research_source import (
    ResearchSource,
)


SearchTopic = Literal[
    "general",
    "news",
    "finance",
]

TimeRange = Literal[
    "day",
    "week",
    "month",
    "year",
]


class ResearchSearchService:
    """
    企业研究搜索服务。

    负责：
    1. 调用 Tavily
    2. 解析 Provider Response
    3. 转换为统一 ResearchSource
    """

    def search(
        self,
        query: str,
        topic: SearchTopic = "general",
        time_range: TimeRange | None = None,
        max_results: int = 5,
    ) -> list[ResearchSource]:

        max_results = max(
            1,
            min(max_results, 8),
        )


        kwargs = {
            "max_results": max_results,

            "topic": topic,

            "search_depth": "basic",

            "include_answer": False,

            "include_raw_content": False,
        }


        if time_range is not None:
            kwargs[
                "time_range"
            ] = time_range


        search_tool = TavilySearch(
            **kwargs
        )


        raw_result = search_tool.invoke(
            {
                "query": query
            }
        )


        results = self._extract_results(
            raw_result
        )


        retrieved_at = datetime.now(
            timezone.utc
        ).isoformat()


        sources = []


        for item in results:

            url = item.get(
                "url"
            )

            if not url:
                continue


            source = ResearchSource(
                # SourceStore 后面重新分配
                source_id="TEMP",

                title=(
                    item.get("title")
                    or "Untitled"
                ),

                url=url,

                snippet=(
                    item.get("content")
                    or ""
                ),

                score=item.get(
                    "score"
                ),

                published_at=(
                    item.get(
                        "published_date"
                    )
                    or item.get(
                        "published_at"
                    )
                ),

                query=query,

                topic=topic,

                retrieved_at=(
                    retrieved_at
                ),
            )

            sources.append(source)


        return sources


    @staticmethod
    def _extract_results(
        raw_result,
    ) -> list[dict]:
        """
        兼容 Tavily Tool 不同版本的返回形式。
        """

        if isinstance(
            raw_result,
            dict,
        ):

            results = raw_result.get(
                "results"
            )

            if isinstance(
                results,
                list,
            ):
                return results

            return []


        if isinstance(
            raw_result,
            list,
        ):
            return raw_result


        if isinstance(
            raw_result,
            str,
        ):

            try:

                parsed = json.loads(
                    raw_result
                )

                if isinstance(
                    parsed,
                    dict,
                ):
                    return parsed.get(
                        "results",
                        []
                    )

                if isinstance(
                    parsed,
                    list,
                ):
                    return parsed

            except json.JSONDecodeError:
                return []


        return []