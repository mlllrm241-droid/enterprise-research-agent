from typing import Literal

from app.rag.vector_store import (
    get_knowledge_vector_store,
)
from app.schemas.knowledge_evidence import (
    KnowledgeEvidence,
)


class KnowledgeRetrievalService:

    def __init__(self):

        self.vector_store = (
            get_knowledge_vector_store()
        )


    def retrieve(
        self,
        query: str,
        k: int = 5,
        search_type: Literal[
            "similarity",
            "mmr",
        ] = "similarity",
    ) -> list[KnowledgeEvidence]:

        k = max(
            1,
            min(k, 8),
        )


        if search_type == "mmr":

            documents = (
                self.vector_store
                .max_marginal_relevance_search(
                    query=query,

                    k=k,

                    fetch_k=max(
                        k * 4,
                        12,
                    ),

                    lambda_mult=0.5,
                )
            )

        else:

            documents = (
                self.vector_store
                .similarity_search(
                    query=query,
                    k=k,
                )
            )


        evidences = []


        for doc in documents:

            metadata = doc.metadata


            evidences.append(
                KnowledgeEvidence(
                    evidence_id=(
                        metadata[
                            "evidence_id"
                        ]
                    ),

                    document_id=(
                        metadata[
                            "document_id"
                        ]
                    ),

                    title=(
                        metadata.get(
                            "title",
                            "Unknown",
                        )
                    ),

                    source_file=(
                        metadata[
                            "source_file"
                        ]
                    ),

                    chunk_index=int(
                        metadata[
                            "chunk_index"
                        ]
                    ),

                    page_number=(
                        metadata.get(
                            "page_number"
                        )
                    ),

                    content=(
                        doc.page_content
                    ),

                    query=query,
                )
            )


        return evidences