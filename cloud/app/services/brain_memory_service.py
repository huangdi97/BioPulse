"""脑记忆服务，统一接口封装工作记忆、情景记忆、语义记忆与程序记忆操作。"""

from typing import Optional

from cloud.app.services.base import BaseService
from cloud.app.services.memory_retriever import MemoryRetriever
from cloud.app.services.memory_writer import MemoryWriter


class BrainMemoryService(BaseService):
    """脑记忆门面服务，聚合 MemoryWriter 和 MemoryRetriever 提供多类型记忆读写。"""

    def __init__(self, db):
        super().__init__(db)
        self._writer = MemoryWriter(self.db)
        self._retriever = MemoryRetriever(self.db)

    def working_set(
        self,
        session_id: str,
        slot_key: str,
        slot_value: str,
        slot_type: str,
        ttl_seconds: int,
    ) -> dict:
        return self._writer.working_set(session_id, slot_key, slot_value, slot_type, ttl_seconds)

    def working_get(self, session_id: str, slot_key: Optional[str] = None) -> dict:
        return self._retriever.working_get(session_id, slot_key)

    def working_clear(self, session_id: str) -> str:
        return self._writer.working_clear(session_id)

    def working_refresh(self, session_id: str) -> dict:
        return self._writer.working_refresh(session_id)

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
        related_entity_id: Optional[int],
        uid: str,
    ) -> dict:
        return self._writer.episodic_store(
            event_type,
            title,
            description,
            context,
            outcome,
            valence,
            intensity,
            involved_agents,
            related_entity_type,
            related_entity_id,
            uid,
        )

    def episodic_list(
        self,
        event_type: Optional[str] = None,
        outcome: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        return self._retriever.episodic_list(event_type, outcome, date_from, date_to, page, page_size)

    def episodic_detail(self, memory_id: int) -> dict:
        return self._retriever.episodic_detail(memory_id)

    def episodic_consolidate(self, memory_id: int, auth_header: str) -> dict:
        return self._writer.episodic_consolidate(memory_id, auth_header)

    def dashboard(self) -> dict:
        return self._retriever.dashboard()

    def semantic_abstract(
        self,
        source_type: str,
        source_id: str,
        abstraction_level: str,
        auth_header: str = "",
    ) -> dict:
        return self._writer.semantic_abstract(source_type, source_id, abstraction_level, auth_header)

    def semantic_search(self, query: str, limit: int = 10) -> dict:
        return self._retriever.semantic_search(query, limit)

    def procedural_learn(
        self,
        pattern_name: str,
        trigger_conditions: str,
        action_sequence: str,
        success_rate: float,
    ) -> dict:
        return self._writer.procedural_learn(pattern_name, trigger_conditions, action_sequence, success_rate)

    def procedural_recall(self, trigger_context: str) -> dict:
        return self._retriever.procedural_recall(trigger_context)

    def memory_decay(self, hours_threshold: int = 72) -> dict:
        return self._writer.memory_decay(hours_threshold)

    def holographic_get(self, memory_id: int, depth: int = 3) -> dict:
        return self._retriever.holographic_get(memory_id, depth)
