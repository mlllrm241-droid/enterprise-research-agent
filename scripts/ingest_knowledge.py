from dotenv import load_dotenv

load_dotenv()

from app.rag.ingestion import (
    KnowledgeIngestionService,
)


def main():

    service = (
        KnowledgeIngestionService()
    )


    result = service.ingest_all()


    print("=" * 60)

    print(
        "Enterprise Knowledge Base"
    )

    print("=" * 60)

    print(
        f"重新索引文档："
        f"{result['indexed']}"
    )

    print(
        f"未变化文档："
        f"{result['skipped']}"
    )

    print(
        f"已删除文档："
        f"{result['deleted']}"
    )

    print(
        f"新增 Chunk："
        f"{result['chunks']}"
    )


if __name__ == "__main__":
    main()