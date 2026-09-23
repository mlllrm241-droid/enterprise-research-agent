from urllib.parse import (
    parse_qsl,
    urlencode,
    urlsplit,
    urlunsplit,
)

from app.schemas.research_source import (
    ResearchSource,
)
from app.workspace.manager import TaskWorkspace


class SourceStore:
    """
    管理一个 Todo 对应的 Research Sources。
    """

    def __init__(
        self,
        task_id: str,
        todo_id: str,
    ):
        self.task_id = task_id
        self.todo_id = todo_id

        self.workspace = TaskWorkspace(
            task_id=task_id
        )

        self.path = (
            f"sources/{todo_id}.json"
        )


    @staticmethod
    def _normalize_url(
        url: str,
    ) -> str:
        """
        去掉 fragment 和常见追踪参数，
        用于简单 URL 去重。
        """

        try:
            parts = urlsplit(url)

            ignored_params = {
                "utm_source",
                "utm_medium",
                "utm_campaign",
                "utm_term",
                "utm_content",
                "gclid",
                "fbclid",
            }

            query = [
                (key, value)
                for key, value
                in parse_qsl(
                    parts.query,
                    keep_blank_values=True,
                )
                if key.lower()
                not in ignored_params
            ]

            normalized = urlunsplit(
                (
                    parts.scheme,
                    parts.netloc,
                    parts.path.rstrip("/"),
                    urlencode(query),
                    "",
                )
            )

            return normalized

        except Exception:
            return url


    def _load(self) -> dict:
        """
        读取当前 Todo 的 Source Store。
        """

        if not self.workspace.exists(
            self.path
        ):
            return {
                "todo_id": self.todo_id,
                "sources": [],
            }

        return self.workspace.read_json(
            self.path
        )


    def save_sources(
        self,
        sources: list[ResearchSource],
    ) -> list[ResearchSource]:
        """
        保存并按照 URL 去重。

        返回本次搜索最终对应的 Source。
        """

        data = self._load()

        existing_sources = data[
            "sources"
        ]

        url_map = {}

        max_number = 0

        for source in existing_sources:

            normalized_url = (
                self._normalize_url(
                    source["url"]
                )
            )

            url_map[
                normalized_url
            ] = source

            try:
                number = int(
                    source["source_id"]
                    .split("-S")[-1]
                )

                max_number = max(
                    max_number,
                    number,
                )

            except Exception:
                pass


        current_sources = []


        for source in sources:

            normalized_url = (
                self._normalize_url(
                    source.url
                )
            )


            if normalized_url in url_map:

                existing = url_map[
                    normalized_url
                ]

                old_score = (
                    existing.get("score")
                    or 0
                )

                new_score = (
                    source.score
                    or 0
                )

                if new_score > old_score:

                    existing["score"] = (
                        source.score
                    )

                    existing["snippet"] = (
                        source.snippet
                    )

                current_sources.append(
                    ResearchSource(
                        **existing
                    )
                )

                continue


            max_number += 1

            source.source_id = (
                f"{self.todo_id}"
                f"-S{max_number:03d}"
            )

            source_dict = (
                source.model_dump()
            )

            existing_sources.append(
                source_dict
            )

            url_map[
                normalized_url
            ] = source_dict

            current_sources.append(
                source
            )


        self.workspace.write_json(
            self.path,
            {
                "todo_id": self.todo_id,

                "sources": existing_sources,
            },
        )


        return current_sources