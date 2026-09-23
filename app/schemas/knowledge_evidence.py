from pydantic import BaseModel


class KnowledgeEvidence(BaseModel):
    """
    从企业内部知识库检索得到的一条证据。
    """

    evidence_id: str

    document_id: str

    title: str

    source_file: str

    chunk_index: int

    page_number: int | None = None

    content: str

    query: str