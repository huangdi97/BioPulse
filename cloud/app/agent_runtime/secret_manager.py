"""密钥管理器。基于加密的 SQLite 存储，可运行时更新无需重启。"""

import json
import logging
import os
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    logger.warning("cryptography not installed, secrets will be stored in plaintext")


def _get_storage_key() -> bytes:
    key_hex = os.environ.get("SECRET_STORAGE_KEY", "")
    if key_hex:
        return bytes.fromhex(key_hex)
    return os.urandom(32)


class SecretManager:
    """密钥管理器。当前基于加密的 SQLite 存储，未来可对接 Vault/AWS Secrets Manager。"""

    def __init__(self, db_path: str = ""):
        self._storage_key = _get_storage_key()
        self._local_db = None
        self._external_db = None
        if db_path:
            self.db_path = db_path
        else:
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            self.db_path = os.path.join(base, "data", "agent_secrets.db")
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
        self._external_db = db

    def _ensure_table(self):
        conn = self._get_connection()
        conn.execute(
            "CREATE TABLE IF NOT EXISTS agent_secrets ("
            "key_name TEXT PRIMARY KEY, "
            "encrypted_value BLOB, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
            "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS agent_secrets_history ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "key_name TEXT NOT NULL, "
            "encrypted_value BLOB, "
            "rotated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        conn.commit()

    def _encrypt(self, plaintext: str) -> bytes:
        if HAS_CRYPTO:
            aesgcm = AESGCM(self._storage_key)
            nonce = os.urandom(12)
            ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
            return json.dumps({"nonce": nonce.hex(), "ct": ct.hex()}).encode("utf-8")
        return plaintext.encode("utf-8")

    def _decrypt(self, blob: bytes) -> str:
        if HAS_CRYPTO:
            try:
                data = json.loads(blob.decode("utf-8"))
                aesgcm = AESGCM(self._storage_key)
                return aesgcm.decrypt(bytes.fromhex(data["nonce"]), bytes.fromhex(data["ct"]), None).decode("utf-8")
            except Exception:
                return blob.decode("utf-8")
        return blob.decode("utf-8")

    def set(self, key_name: str, value: str):
        conn = self._get_connection()
        now = datetime.now().isoformat()
        encrypted = self._encrypt(value)
        existing = conn.execute("SELECT encrypted_value FROM agent_secrets WHERE key_name=?", (key_name,)).fetchone()
        if existing:
            conn.execute(
                "INSERT INTO agent_secrets_history (key_name, encrypted_value) VALUES (?, ?)",
                (key_name, existing["encrypted_value"] if isinstance(existing, sqlite3.Row) else existing[0]),
            )
        conn.execute(
            "INSERT OR REPLACE INTO agent_secrets (key_name, encrypted_value, updated_at) VALUES (?, ?, ?)",
            (key_name, encrypted, now),
        )
        conn.commit()
        logger.info("Secret %s updated", key_name)

    def get(self, key_name: str) -> str | None:
        conn = self._get_connection()
        row = conn.execute("SELECT encrypted_value FROM agent_secrets WHERE key_name=?", (key_name,)).fetchone()
        if not row:
            return None
        return self._decrypt(row["encrypted_value"])

    def list_keys(self) -> list[str]:
        conn = self._get_connection()
        rows = conn.execute("SELECT key_name FROM agent_secrets ORDER BY key_name").fetchall()
        return [r["key_name"] for r in rows]

    def rotate(self, key_name: str, new_value: str):
        self.set(key_name, new_value)

    def delete(self, key_name: str):
        conn = self._get_connection()
        conn.execute("DELETE FROM agent_secrets WHERE key_name=?", (key_name,))
        conn.commit()
