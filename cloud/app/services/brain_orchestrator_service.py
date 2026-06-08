"""脑编排服务，承接感知输入并协调多类型记忆存储与编排推理。"""

import json
from datetime import datetime, timedelta

from cloud.app.services.base import BaseService


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


KEYWORD_MAP = [
    (["urgent", "紧急", "违规", "violation"], 0.85, 0.9),
    (["商机", "签约", "opportunity", "deal"], 0.75, 0.85),
    (["投诉", "complain", "风险", "risk"], 0.7, 0.8),
]


def _calc_importance(text: str) -> float:
    """基于关键词计算文本重要性。

    Args:
        text: 输入文本

    Returns:
        重要性分数（0-1）
    """
    lower = text.lower()
    for keywords, lo, hi in KEYWORD_MAP:
        if any(kw in lower or kw in text for kw in keywords):
            import random

            return round(random.uniform(lo, hi), 2)
    return round(random.uniform(0.1, 0.3), 2)


class BrainOrchestratorService(BaseService):
    """脑编排服务，提供感知输入摄取、多级记忆路由与编排推理功能。"""

    def ingest_sensory(self, input_type: str, raw_content: str, source: str) -> dict:
        """摄取感知输入并根据重要性路由到不同记忆层。

        Args:
            input_type: 输入类型
            raw_content: 原始内容
            source: 来源

        Returns:
            含 sensory_id、importance 和 routed_to 的摄取结果
        """
        importance = _calc_importance(raw_content)
        n = _now()
        expires_at = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        cur = self.db.execute(
            "INSERT INTO sensory_memory (input_type, raw_content, source, importance, expires_at, created_at) VALUES (?,?,?,?,?,?)",
            (input_type, raw_content, source, importance, expires_at, n),
        )
        sid = cur.lastrowid
        routed_to = ["sensory_memory"]
        if importance > 0.6:
            self.db.execute(
                "INSERT OR REPLACE INTO working_memory (session_id, slot_key, slot_value, slot_type, ttl_seconds, created_at, expires_at) VALUES (?,?,?,?,?,?,?)",
                ("brain_orchestrator", f"sensory_{sid}", raw_content[:500], "string", 1800, n, expires_at),
            )
            self.db.execute(
                "INSERT INTO memory_consolidation_log (consolidation_type, source_table, item_count, items_promoted, status, details, created_at) VALUES (?,?,?,?,?,?,?)",
                (
                    "sensory_promotion",
                    "sensory_memory",
                    1,
                    1,
                    "completed",
                    json.dumps({"sensory_id": sid, "importance": importance}, ensure_ascii=False),
                    n,
                ),
            )
            routed_to.append("working_memory")
        if importance > 0.8:
            self.db.execute(
                "INSERT INTO episodic_memory (event_type, title, description, context, outcome, valence, intensity, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    "sensory_triggered",
                    f"Sensory->Episodic #{sid}",
                    raw_content[:300],
                    json.dumps({"source": source, "sensory_id": sid}, ensure_ascii=False),
                    "auto_ingested",
                    importance,
                    0.6,
                    "0",
                    n,
                ),
            )
            routed_to.append("episodic_memory")
        self.db.commit()
        return {"sensory_id": sid, "importance": importance, "processed": 0, "routed_to": routed_to}

    def get_sensory_buffer(self, limit: int = 50) -> list[dict]:
        """获取未过期的感知缓冲区记录。

        Args:
            limit: 最大返回数

        Returns:
            感知记录列表（按重要性降序）
        """
        n = _now()
        rows = self.db.execute(
            "SELECT * FROM sensory_memory WHERE (expires_at = '' OR expires_at > ?) ORDER BY importance DESC LIMIT ?",
            (n, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_procedural(self, trigger_event: str | None = None) -> list[dict]:
        """列出程序性记忆。

        Args:
            trigger_event: 按触发条件筛选

        Returns:
            程序性记忆列表（按调用次数降序）
        """
        if trigger_event:
            rows = self.db.execute(
                "SELECT * FROM procedural_memory WHERE trigger_conditions LIKE ? ORDER BY invocation_count DESC",
                (f"%{trigger_event}%",),
            ).fetchall()
        else:
            rows = self.db.execute("SELECT * FROM procedural_memory ORDER BY invocation_count DESC").fetchall()
        return [dict(r) for r in rows]

    def create_procedural(self, procedure_key: str, name: str, description: str, steps: str, trigger_conditions: str) -> dict:
        """创建程序性记忆条目。

        Args:
            procedure_key: 唯一键
            name: 名称
            description: 描述
            steps: 步骤（JSON 字符串）
            trigger_conditions: 触发条件

        Returns:
            创建的程序性记忆基本信息
        """
        n = _now()
        self.db.execute(
            "INSERT INTO procedural_memory (procedure_key, name, description, steps, trigger_conditions, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            (procedure_key, name, description, steps, trigger_conditions, n, n),
        )
        self.db.commit()
        return {"procedure_key": procedure_key, "name": name, "created_at": n}

    def invoke_procedural(self, procedure_key: str, context: dict) -> dict:
        """调用程序性记忆并增加调用计数。

        Args:
            procedure_key: 唯一键
            context: 执行上下文

        Returns:
            含步骤和调用计数的执行结果
        """
        row = self.db.execute("SELECT * FROM procedural_memory WHERE procedure_key=?", (procedure_key,)).fetchone()
        if not row:
            return {"error": f"procedure '{procedure_key}' not found"}
        row = dict(row)
        n = _now()
        new_count = (row["invocation_count"] or 0) + 1
        self.db.execute(
            "UPDATE procedural_memory SET invocation_count=?, last_invoked_at=?, updated_at=? WHERE procedure_key=?",
            (new_count, n, n, procedure_key),
        )
        self.db.commit()
        steps_data = json.loads(row["steps"]) if isinstance(row["steps"], str) else row["steps"]
        return {
            "procedure_key": procedure_key,
            "name": row["name"],
            "steps": steps_data,
            "step_count": len(steps_data),
            "invocation_count": new_count,
            "last_invoked_at": n,
            "context": context,
            "status": "ready",
        }

    def orchestrate(self, input_text: str, input_type: str, source: str) -> dict:
        """执行完整的记忆编排：感知→工作→情景→语义→程序→情绪。

        Args:
            input_text: 输入文本
            input_type: 输入类型
            source: 来源

        Returns:
            各记忆层查询结果的综合字典
        """
        n = _now()
        sensory = self.ingest_sensory(input_type, input_text, source)
        working = [
            dict(r)
            for r in self.db.execute(
                "SELECT * FROM working_memory WHERE session_id=? AND expires_at>? ORDER BY created_at DESC LIMIT 5",
                ("brain_orchestrator", n),
            ).fetchall()
        ]
        episodic = [dict(r) for r in self.db.execute("SELECT * FROM episodic_memory ORDER BY valence DESC LIMIT 5").fetchall()]
        kg_rows = self.db.execute(
            "SELECT * FROM kg_entities WHERE name LIKE ? OR entity_type LIKE ? LIMIT 5",
            (f"%{input_text[:20]}%", f"%{input_text[:20]}%"),
        ).fetchall()
        semantic_kv = [dict(r) for r in kg_rows] if kg_rows else []
        proc_rows = self.db.execute("SELECT * FROM procedural_memory WHERE invocation_count > 0 ORDER BY invocation_count DESC LIMIT 3").fetchall()
        procedural = [dict(r) for r in proc_rows]
        valences = [e.get("valence", 0.0) or 0.0 for e in episodic]
        avg_valence = sum(valences) / len(valences) if valences else 0.0
        if avg_valence > 0.3:
            emotional = {"mood": "positive", "valence": round(avg_valence, 2), "utility": 0.7, "label": "积极"}
        elif avg_valence < -0.3:
            emotional = {"mood": "negative", "valence": round(avg_valence, 2), "utility": 0.3, "label": "消极"}
        else:
            emotional = {"mood": "neutral", "valence": round(avg_valence, 2), "utility": 0.5, "label": "中性"}
        return {
            "sensory": sensory,
            "working": working,
            "episodic": episodic,
            "semantic": semantic_kv,
            "procedural": procedural,
            "emotional": emotional,
        }

    def _read_memory(self, memory_id: int, memory_type: str) -> dict | None:
        """读取指定类型的记忆记录。

        Args:
            memory_id: 记忆 ID
            memory_type: 记忆类型（episodic/sensory/procedural）

        Returns:
            记忆记录字典，不存在返回 None
        """
        table_map = {
            "episodic": "episodic_memory",
            "sensory": "sensory_memory",
            "procedural": "procedural_memory",
        }
        table = table_map.get(memory_type)
        if not table:
            return None
        row = self.db.execute(f"SELECT * FROM {table} WHERE id=?", (memory_id,)).fetchone()
        return dict(row) if row else None

    def _update_memory_field(self, memory_id: int, memory_type: str, field: str, new_value: str) -> bool:
        """更新记忆记录的指定字段。

        Args:
            memory_id: 记忆 ID
            memory_type: 记忆类型
            field: 字段名
            new_value: 新值

        Returns:
            更新成功返回 True，失败返回 False
        """
        table_map = {
            "episodic": "episodic_memory",
            "sensory": "sensory_memory",
            "procedural": "procedural_memory",
        }
        table = table_map.get(memory_type)
        if not table:
            return False
        allowed_fields = {
            "episodic": {"title", "description", "context", "outcome", "valence", "intensity"},
            "sensory": {"raw_content", "importance"},
            "procedural": {"name", "description", "steps", "trigger_conditions"},
        }
        allowed = allowed_fields.get(memory_type, set())
        if field not in allowed:
            return False
        quoted = f'"{field}"'
        self.db.execute(
            f"UPDATE {table} SET {quoted}=?, updated_at=? WHERE id=?",
            (new_value, _now(), memory_id),
        )
        return True
