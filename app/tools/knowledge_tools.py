from typing import Literal

from langchain.tools import tool

from app.rag.evidence_store import (
    KnowledgeEvidenceStore,
)
from app.rag.retrieval import (
    KnowledgeRetrievalService,
)


def build_knowledge_tools(
    task_id: str,
    todo_id: str,
):

    retrieval_service = (
        KnowledgeRetrievalService()
    )

    evidence_store = (
        KnowledgeEvidenceStore(
            task_id=task_id,
            todo_id=todo_id,
        )
    )


    @tool
    def knowledge_search(
        query: str,
        k: int = 5,
        search_type: Literal[
            "similarity",
            "mmr",
        ] = "similarity",
    ) -> str:
        """
        搜索企业内部知识库。

        适合查询企业内部制度、标准、业务规则、
        研究规范、产品文档和其他已经入库的内部资料。

        参数:
            query:
                需要检索的问题。

            k:
                返回的知识片段数量。

            search_type:
                similarity 或 mmr。
        """

        evidences = (
            retrieval_service.retrieve(
                query=query,
                k=k,
                search_type=search_type,
            )
        )


        if not evidences:

            return (
                "企业内部知识库中"
                "没有找到相关证据。"
            )


        evidence_store.save(
            evidences
        )


        output = [
            (
                f"内部知识检索问题："
                f"{query}\n"
                f"共找到 "
                f"{len(evidences)} 条证据。"
            )
        ]


        for evidence in evidences:

            page_text = ""

            if (
                evidence.page_number
                is not None
            ):

                page_text = (
                    f"\n页码："
                    f"{evidence.page_number}"
                )


            output.append(
                f"""
[{evidence.evidence_id}]
文档：{evidence.title}
源文件：{evidence.source_file}{page_text}

内容：
{evidence.content}
""".strip()
            )


        return "\n\n".join(
            output
        )


    return [
        knowledge_search
    ]