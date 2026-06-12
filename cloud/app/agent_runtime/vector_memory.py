"""轻量级向量记忆，用于 Agent 的语义检索。"""

import json
import logging
import os
import sqlite3
import struct
from datetime import datetime

logger = logging.getLogger(__name__)


class VectorMemory:
    """轻量级向量记忆，用于 Agent 的语义检索。使用 sentence-transformers 嵌入 + SQLite 存储。"""

    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    def __init__(self, db_path: str = ""):
        self.db_path = db_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "data",
            "agent_vector_memory.db",
        )
        self._model = None
        self._local_db = None
        self._external_db = None
        self._ensure_table()

    def _get_connection(self) -> sqlite3.Connection:
        if self._external_db is not None:
            return self._external_db
        if self._local_db is None:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self._local_db = sqlite3.connect(self.db_path)
            self._local_db.row_factory = sqlite3.Row
        return self._local_db

    def set_db(self, db):
        """设置外部数据库连接。"""
        self._external_db = db
        self._ensure_table()

    def _ensure_table(self):
        try:
            conn = self._get_connection()
            conn.execute(
                "CREATE TABLE IF NOT EXISTS agent_vector_memory ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "agent_name TEXT NOT NULL, "
                "key TEXT NOT NULL, "
                "content TEXT NOT NULL, "
                "embedding BLOB, "
                "metadata TEXT DEFAULT '{}', "
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
                "UNIQUE(agent_name, key)"
                ")"
            )
            conn.commit()
        except Exception:
            logger.exception("Failed to ensure vector memory table")

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.EMBEDDING_MODEL)
            except ImportError:
                logger.warning("sentence-transformers not installed, using fallback embedding")
                self._model = None
        return self._model

    def _get_embedding(self, text: str) -> list[float]:
        model = self._get_model()
        if model is not None:
            return model.encode(text, normalize_embeddings=True).tolist()
        return [0.0] * 384

    def _serialize_embedding(self, embedding: list[float]) -> bytes:
        return struct.pack(f"{len(embedding)}f", *embedding)

    def _deserialize_embedding(self, blob: bytes) -> list[float]:
        return list(struct.unpack(f"{len(blob) // 4}f", blob))

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        return dot

    def store(self, agent_name: str, key: str, content: str, metadata: dict = None):
        """存储向量记忆条目。"""
        embedding = self._get_embedding(content)
        conn = self._get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO agent_vector_memory (agent_name, key, content, embedding, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                agent_name,
                key,
                content,
                self._serialize_embedding(embedding),
                json.dumps(metadata or {}, ensure_ascii=False),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()

    def search(self, agent_name: str, query: str, top_k: int = 5) -> list[dict]:
        """语义搜索向量记忆。"""
        query_emb = self._get_embedding(query)
        conn = self._get_connection()
        rows = conn.execute(
            "SELECT key, content, metadata, created_at FROM agent_vector_memory WHERE agent_name=?",
            (agent_name,),
        ).fetchall()
        scored = []
        for row in rows:
            stored_emb = self._deserialize_embedding(row["embedding"]) if row["embedding"] else [0.0] * 384
            score = self._cosine_similarity(query_emb, stored_emb)
            scored.append(
                (
                    score,
                    {
                        "key": row["key"],
                        "content": row["content"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                        "created_at": row["created_at"],
                        "score": round(score, 4),
                    },
                )
            )
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    def recall(self, agent_name: str, key: str) -> str | None:
        """按 key 精确召回向量记忆内容。"""
        conn = self._get_connection()
        row = conn.execute(
            "SELECT content FROM agent_vector_memory WHERE agent_name=? AND key=?",
            (agent_name, key),
        ).fetchone()
        return row["content"] if row else None
