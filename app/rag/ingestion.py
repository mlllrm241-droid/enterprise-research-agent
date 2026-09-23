import hashlib
import json
import os

from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
)
from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

from app.rag.vector_store import (
    get_knowledge_vector_store,
)


class KnowledgeIngestionService:
    """
    企业知识库构建服务。
    """

    SUPPORTED_SUFFIXES = {
        ".txt",
        ".md",
        ".pdf",
    }


    def __init__(self):

        self.raw_dir = Path(
            os.getenv(
                "RAG_RAW_DIR",
                "knowledge/raw",
            )
        )

        self.manifest_path = Path(
            "knowledge/manifest.json"
        )

        self.vector_store = (
            get_knowledge_vector_store()
        )

        self.splitter = (
            RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap=120,

                separators=[
                    "\n\n",
                    "\n",
                    "。",
                    "！",
                    "？",
                    ". ",
                    " ",
                    "",
                ],

                add_start_index=True,
            )
        )


    def ingest_all(self) -> dict:
        """
        扫描知识库目录并进行增量索引。
        """

        self.raw_dir.mkdir(
            parents=True,
            exist_ok=True,
        )


        manifest = self._load_manifest()

        existing_files = set()

        statistics = {
            "indexed": 0,
            "skipped": 0,
            "deleted": 0,
            "chunks": 0,
        }


        paths = sorted(
            path
            for path in self.raw_dir.rglob("*")
            if (
                path.is_file()
                and path.suffix.lower()
                in self.SUPPORTED_SUFFIXES
            )
        )


        for path in paths:

            relative_path = (
                path
                .relative_to(self.raw_dir)
                .as_posix()
            )

            existing_files.add(
                relative_path
            )


            file_hash = (
                self._hash_file(path)
            )


            previous = (
                manifest["documents"]
                .get(relative_path)
            )


            # 文件没有变化
            if (
                previous
                and previous["sha256"]
                == file_hash
            ):

                statistics[
                    "skipped"
                ] += 1

                continue


            # 文件发生过修改
            if previous:

                old_chunk_ids = (
                    previous.get(
                        "chunk_ids",
                        [],
                    )
                )

                if old_chunk_ids:

                    self.vector_store.delete(
                        ids=old_chunk_ids
                    )


            raw_documents = (
                self._load_file(path)
            )


            document_id = (
                self._create_document_id(
                    relative_path
                )
            )


            chunks = (
                self.splitter
                .split_documents(
                    raw_documents
                )
            )


            documents = []

            chunk_ids = []


            for index, chunk in enumerate(
                chunks,
                start=1,
            ):

                evidence_id = (
                    f"KB-{document_id}"
                    f"-C{index:03d}"
                )


                page_number = None

                raw_page = (
                    chunk.metadata.get(
                        "page"
                    )
                )

                if isinstance(
                    raw_page,
                    int,
                ):
                    page_number = (
                        raw_page + 1
                    )


                metadata = {
                    "evidence_id":
                        evidence_id,

                    "document_id":
                        document_id,

                    "source_file":
                        relative_path,

                    "title":
                        path.stem,

                    "chunk_index":
                        index,

                    "sha256":
                        file_hash,
                }


                if page_number is not None:

                    metadata[
                        "page_number"
                    ] = page_number


                start_index = (
                    chunk.metadata.get(
                        "start_index"
                    )
                )

                if isinstance(
                    start_index,
                    int,
                ):
                    metadata[
                        "start_index"
                    ] = start_index


                documents.append(
                    Document(
                        page_content=(
                            chunk.page_content
                        ),

                        metadata=metadata,
                    )
                )

                chunk_ids.append(
                    evidence_id
                )


            if documents:

                self.vector_store.add_documents(
                    documents=documents,
                    ids=chunk_ids,
                )


            manifest[
                "documents"
            ][relative_path] = {
                "document_id":
                    document_id,

                "sha256":
                    file_hash,

                "chunk_ids":
                    chunk_ids,
            }


            statistics[
                "indexed"
            ] += 1

            statistics[
                "chunks"
            ] += len(
                chunk_ids
            )


        # 删除已经不存在的源文件
        old_files = set(
            manifest["documents"].keys()
        )


        removed_files = (
            old_files
            - existing_files
        )


        for relative_path in (
            removed_files
        ):

            previous = (
                manifest[
                    "documents"
                ][relative_path]
            )

            chunk_ids = (
                previous.get(
                    "chunk_ids",
                    [],
                )
            )

            if chunk_ids:

                self.vector_store.delete(
                    ids=chunk_ids
                )


            del manifest[
                "documents"
            ][relative_path]


            statistics[
                "deleted"
            ] += 1


        self._save_manifest(
            manifest
        )


        return statistics


    def _load_file(
        self,
        path: Path,
    ) -> list[Document]:

        suffix = (
            path.suffix.lower()
        )


        if suffix in {
            ".txt",
            ".md",
        }:

            loader = TextLoader(
                str(path),
                encoding="utf-8",
            )

            return loader.load()


        if suffix == ".pdf":

            loader = PyPDFLoader(
                str(path)
            )

            return loader.load()


        raise ValueError(
            f"不支持的文件类型: "
            f"{suffix}"
        )


    @staticmethod
    def _hash_file(
        path: Path,
    ) -> str:

        sha256 = hashlib.sha256()

        with path.open("rb") as f:

            while chunk := f.read(
                1024 * 1024
            ):

                sha256.update(
                    chunk
                )

        return sha256.hexdigest()


    @staticmethod
    def _create_document_id(
        relative_path: str,
    ) -> str:

        value = hashlib.sha1(
            relative_path
            .lower()
            .encode("utf-8")
        ).hexdigest()[:8]

        return (
            f"D{value.upper()}"
        )


    def _load_manifest(
        self,
    ) -> dict:

        if not self.manifest_path.exists():

            return {
                "documents": {}
            }


        return json.loads(
            self.manifest_path.read_text(
                encoding="utf-8"
            )
        )


    def _save_manifest(
        self,
        manifest: dict,
    ) -> None:

        self.manifest_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.manifest_path.write_text(
            json.dumps(
                manifest,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )