import json
import os
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.rag.embeddings import get_embedding_model
from app.schemas.memory import ResearchEpisode, UserMemoryProfile


class LongTermMemoryStore:
    def __init__(self, user_id: str):
        # =========================================
        # 1. 初始化用户信息
        # =========================================
        self.user_id = user_id

        # =========================================
        # 2. 初始化 Profile 路径
        # =========================================
        profile_dir = Path(os.getenv("MEMORY_PROFILE_DIR", "memory/profiles"))
        profile_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path = profile_dir / f"{user_id}.json"

        # =========================================
        # 3. 初始化 Episodic Vector Store
        # =========================================
        self.vector_store = Chroma(
            collection_name=os.getenv(
                "MEMORY_COLLECTION_NAME",
                "enterprise_research_memory",
            ),
            embedding_function=get_embedding_model(),
            persist_directory=os.getenv(
                "MEMORY_PERSIST_DIR",
                "data/memory_chroma",
            ),
        )

    def load_profile(self) -> UserMemoryProfile:
        # =========================================
        # 1. Profile 不存在则返回默认值
        # =========================================
        if not self.profile_path.exists():
            return UserMemoryProfile()

        # =========================================
        # 2. 加载 Profile
        # =========================================
        data = json.loads(self.profile_path.read_text(encoding="utf-8"))
        return UserMemoryProfile.model_validate(data)

    def save_profile(self, profile: UserMemoryProfile) -> None:
        # =========================================
        # 1. 保存用户长期偏好
        # =========================================
        self.profile_path.write_text(
            profile.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def save_episode(self, episode: ResearchEpisode) -> None:
        # =========================================
        # 1. 构建 Memory Document
        # =========================================
        document = Document(
            page_content=(
                f"研究任务：{episode.user_query}\n"
                f"主题：{', '.join(episode.topics)}\n"
                f"研究摘要：{episode.summary}"
            ),
            metadata={
                "user_id": self.user_id,
                "task_id": episode.task_id,
                "review_status": episode.review_status,
                "created_at": episode.created_at,
                "report_path": episode.final_report_path,
            },
        )

        # =========================================
        # 2. 避免同一 Task 重复保存
        # =========================================
        existing = self.vector_store.get_by_ids([episode.task_id])

        if existing:
            self.vector_store.update_document(
                episode.task_id,
                document,
            )
        else:
            self.vector_store.add_documents(
                documents=[document],
                ids=[episode.task_id],
            )

    def search_episodes(self, query: str, k: int = 3):
        # =========================================
        # 1. 搜索当前用户历史研究
        # =========================================
        return self.vector_store.similarity_search(
            query=query,
            k=k,
            filter={"user_id": self.user_id},
        )