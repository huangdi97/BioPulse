"""情景记忆写入、AI 驱动的记忆抽象与长期记忆巩固，及自动关联触发。"""

import json
import urllib.request
from collections.abc import Callable

from cloud.app.repositories import (
    EpisodicMemoryRepository,
    MemoryConsolidationLogRepository,
    MemoryEntriesRepository,
)
from shared.ai_gateway import LLM_INFERENCE_TIMEOUT
from shared.config import settings as config_settings
from shared.datetime_utils import now as _now


def _call_ai(messages: list[dict], auth_header: str) -> dict:
    payload = {"messages": messages, "temperature": 0.3, "max_tokens": 2048}
    req = urllib.request.Request(
        f"{config_settings.ai_chat_url}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": auth_header},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=LLM_INFERENCE_TIMEOUT) as rp:
        return json.loads(rp.read().decode("utf-8")).get("data", {})


def build_consolidation_prompt(row):
    """构建记忆巩固的 AI 提示词，引导模型提炼情景记忆为结构化洞察。"""
    return [
        {
            "role": "system",
            "content": "你是一名记忆巩固专家。请根据输入的情景记忆内容，提炼核心洞察，生成结构化的记忆条目。"
            '输出纯JSON（不要markdown代码块）：{"title":"洞察标题","content":"详细内容","memory_type":"insight",'
            '"importance":0.8,"context_tags":["标签1","标签2"]}',
        },
        {
            "role": "user",
            "content": f"事件类型: {row['event_type']}\n标题: {row['title']}\n"
            f"描述: {row['description']}\n情景: {row['context']}\n结果: {row['outcome']}\n"
            f"情感值: {row['valence']}\n强度: {row['intensity']}",
        },
    ]


def parse_consolidation_reply(reply, row):
    """解析 AI 巩固回复为结构化记忆条目，解析失败时回退默认值。"""
    try:
        return json.loads(reply)
    except (json.JSONDecodeError, TypeError):
        return {
            "title": row["title"],
            "content": reply or row["description"],
            "memory_type": "insight",
            "importance": 0.5,
            "context_tags": [],
        }


def build_abstract_prompt(rows, abstraction_level, txt):
    """构建语义抽象的 AI 提示词，按指定抽象层级生成摘要。"""
    return [
        {
            "role": "system",
            "content": f'语义抽象层次={abstraction_level}。输出JSON:{{"title":"","content":"","context_tags":[]}}',
        },
        {"role": "user", "content": txt},
    ]


def parse_abstract_reply(reply, source_type, fallback_txt=""):
    """解析 AI 抽象回复，失败时返回基于源类型的默认结构。"""
    try:
        return json.loads(reply)
    except json.JSONDecodeError:
        return {
            "title": f"Semantic-{source_type}",
            "content": reply or fallback_txt,
            "context_tags": [],
        }


class EpisodicMemoryWriter:
    """负责 episodic_memory 写入，以及从情景记忆生成长期记忆条目。"""

    def __init__(self, db, auto_associate: Callable[[int, dict], None]):
        """初始化 EpisodicMemoryWriter。

        Args:
            db: 数据库连接实例。
            auto_associate: 自动关联回调函数，接收条目 ID 和条目数据。
        """
        self.db = db
        self._auto_associate = auto_associate

    def episodic_store(
        self,
        event_type: str,
        title: str,
        description: str,
        context: dict,
        outcome: str,
        valence: float,
        intensity: float,
        involved_agents: list[str],
        related_entity_type: str,
        related_entity_id: int | None,
        uid: str,
    ) -> dict:
        """存储情景记忆条目并检测干扰性遗忘。"""
        n = _now()
        em = EpisodicMemoryRepository(self._connection())
        new_id = em.create(
            {
                "event_type": event_type,
                "title": title,
                "description": description,
                "context": json.dumps(context, ensure_ascii=False),
                "outcome": outcome,
                "valence": valence,
                "intensity": intensity,
                "involved_agents": json.dumps(involved_agents, ensure_ascii=False),
                "related_entity_type": related_entity_type,
                "related_entity_id": related_entity_id,
                "created_by": uid,
                "created_at": n,
            }
        )
        interference = 0
        if related_entity_id or event_type:
            conds, p = [], []
            if related_entity_id and related_entity_type:
                conds.append("related_entity_id=? AND related_entity_type=?")
                p += [related_entity_id, related_entity_type]
            if event_type:
                conds.append("event_type=?")
                p.append(event_type)
            for old in em.db.execute(
                f"SELECT valence FROM episodic_memory WHERE id!=? AND ({' OR '.join(conds)})",
                [new_id] + p,
            ):
                if (old["valence"] or 0.0) * (valence or 0.0) < 0:
                    interference += 1
        if interference:
            MemoryConsolidationLogRepository(self._connection()).create(
                {
                    "consolidation_type": "interference_forgetting",
                    "source_table": "episodic_memory",
                    "item_count": interference,
                    "items_superseded": interference,
                    "status": "completed",
                    "details": json.dumps({"new_id": new_id, "triggered_by": uid}, ensure_ascii=False),
                    "created_at": n,
                }
            )
        return {
            "id": new_id,
            "event_type": event_type,
            "title": title,
            "description": description,
            "outcome": outcome,
            "valence": valence,
            "intensity": intensity,
            "involved_agents": involved_agents,
            "related_entity_type": related_entity_type,
            "related_entity_id": related_entity_id,
        }

    def episodic_consolidate(self, memory_id: int, auth_header: str) -> dict:
        """巩固指定情景记忆为长期记忆条目，调用 AI 提炼洞察并触发自动关联。"""
        em_repo = EpisodicMemoryRepository(self._connection())
        me_repo = MemoryEntriesRepository(self._connection())
        row = em_repo.get_by_id(memory_id)
        if not row:
            from fastapi import HTTPException
            from starlette import status

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episodic memory not found")
        if row["is_consolidated"]:
            from fastapi import HTTPException
            from starlette import status

            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already consolidated")
        messages = build_consolidation_prompt(row)
        ai_result = _call_ai(messages, auth_header)
        reply = ai_result.get("reply", "")
        insight = parse_consolidation_reply(reply, row)
        title = insight.get("title", row["title"])
        content = insight.get("content", row["description"])
        memory_type = insight.get("memory_type", "insight")
        importance = float(insight.get("importance", 0.5))
        context_tags = insight.get("context_tags", [])
        if not isinstance(context_tags, list):
            context_tags = []
        now_val = _now()
        entry_id = me_repo.create(
            {
                "title": title,
                "content": content,
                "memory_type": memory_type,
                "source_type": "episodic_consolidation",
                "source_id": f"ep_{memory_id}",
                "importance": min(max(importance, 0.0), 1.0),
                "context_tags": json.dumps(context_tags, ensure_ascii=False),
                "access_count": 0,
                "created_by": 1,
                "created_at": now_val,
                "updated_at": now_val,
            }
        )
        em_repo.update(memory_id, {"is_consolidated": 1})
        fetched = me_repo.get_by_id(entry_id)
        if fetched:
            self._auto_associate(entry_id, fetched)
        return {
            "memory_id": memory_id,
            "entry_id": entry_id,
            "title": title,
            "memory_type": memory_type,
            "importance": importance,
        }

    def semantic_abstract(
        self,
        source_type: str,
        source_id: str,
        abstraction_level: str,
        auth_header: str = "",
    ) -> dict:
        """基于情景记忆生成语义抽象条目并触发自动关联。"""
        rows = (
            EpisodicMemoryRepository(self._connection())
            .db.execute(
                "SELECT * FROM episodic_memory WHERE related_entity_type=? AND related_entity_id=? ORDER BY created_at DESC",
                (source_type, int(source_id)),
            )
            .fetchall()
        )
        if not rows:
            from fastapi import HTTPException
            from starlette import status

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episodic memories for abstraction not found")
        txt = "\n".join(f"{r['title']}: {r['description']}" for r in rows)
        msg = build_abstract_prompt(rows, abstraction_level, txt)
        reply = _call_ai(msg, auth_header).get("reply", "")
        d = parse_abstract_reply(reply, source_type, txt[:200])
        n = _now()
        eid = MemoryEntriesRepository(self._connection()).create(
            {
                "title": d.get("title", ""),
                "content": d.get("content", txt[:200]),
                "memory_type": "semantic",
                "source_type": source_type,
                "source_id": str(source_id),
                "importance": 0.7,
                "context_tags": json.dumps(d.get("context_tags", []), ensure_ascii=False),
                "access_count": 0,
                "created_by": 0,
                "created_at": n,
                "updated_at": n,
            }
        )
        fetched = MemoryEntriesRepository(self._connection()).get_by_id(eid)
        if fetched:
            self._auto_associate(eid, fetched)
        return {"id": eid, "title": d.get("title", ""), "content": d.get("content", "")}
