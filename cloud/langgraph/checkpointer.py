"""SqliteSaver-based checkpointer for LangGraph state persistence.

Provides durable checkpoint storage so graph execution state survives
process restarts. Defaults to a local SQLite database file.
"""

import os
import sqlite3
from typing import Optional

from langgraph.checkpoint.sqlite import SqliteSaver


def get_sqlite_checkpointer(db_path: str | None = None) -> SqliteSaver:
    """Create a SqliteSaver checkpoint instance backed by a local SQLite file.

    Args:
        db_path: Path to the SQLite checkpoint database file.
                 Defaults to data/langgraph_checkpoints.db.

    Returns:
        A SqliteSaver instance connected to the specified database.
    """
    if db_path is None:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "langgraph_checkpoints.db",
        )
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return SqliteSaver(conn)


def get_psql_checkpointer(conn_string: Optional[str] = None):
    """返回 PostgresSaver checkpointer。配置连接字符串后可使用。"""
    if conn_string:
        from langgraph.checkpoint.postgres import PostgresSaver

        return PostgresSaver.from_conn_string(conn_string)
    return get_checkpointer()


def get_checkpointer() -> SqliteSaver:
    """Get the default SqliteSaver checkpoint instance."""
    return get_sqlite_checkpointer()
