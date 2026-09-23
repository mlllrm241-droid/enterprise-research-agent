import os

from app.memory.store import LongTermMemoryStore


class LongTermMemoryService:
    def __init__(self, user_id: str):
        # =========================================
        # 1. 初始化 Memory Store
        # =========================================
        self.store = LongTermMemoryStore(user_id)

    def build_memory_context(self, query: str) -> tuple[str, list[str]]:
        # =========================================
        # 1. 加载用户 Profile
        # =========================================
        profile = self.store.load_profile()

        # =========================================
        # 2. 搜索相关历史研究
        # =========================================
        top_k = int(os.getenv("MEMORY_TOP_K", "3"))
        episodes = self.store.search_episodes(query, top_k)

        # =========================================
        # 3. 构建 Profile Context
        # =========================================
        profile_context = f"""
用户长期偏好：
语言：{profile.language}
来源偏好：{", ".join(profile.source_preferences) or "未设置"}
报告偏好：{", ".join(profile.report_preferences) or "未设置"}
""".strip()

        # =========================================
        # 4. 构建 Episode Context
        # =========================================
        episode_context = "\n\n".join(
            f"[Memory:{doc.metadata['task_id']}]\n{doc.page_content}\n"
            f"质量状态：{doc.metadata['review_status']}"
            for doc in episodes
        )

        # =========================================
        # 5. 返回短期注入 Context
        # =========================================
        context = (
            f"{profile_context}\n\n历史相关研究：\n"
            f"{episode_context or '无相关历史研究'}"
        )

        memory_ids = [
            doc.metadata["task_id"]
            for doc in episodes
        ]

        return context, memory_ids