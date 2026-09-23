import os
import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


_connection = None
_checkpointer = None


def get_checkpointer():
    global _connection, _checkpointer

    # =========================================
    # 1. 已创建则直接复用
    # =========================================
    if _checkpointer is not None:
        return _checkpointer

    # =========================================
    # 2. 获取 SQLite 路径
    # =========================================
    db_path = os.getenv(
        "CHECKPOINT_DB",
        "data/checkpoints.sqlite",
    )

    Path(db_path).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # =========================================
    # 3. 创建持久化 Checkpointer
    # =========================================
    _connection = sqlite3.connect(
        db_path,
        check_same_thread=False,
    )

    _checkpointer = SqliteSaver(
        _connection
    )

    return _checkpointer