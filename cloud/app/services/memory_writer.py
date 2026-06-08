"""记忆写入服务门面。"""

from cloud.app.services.base import BaseService
from cloud.app.services.holographic_service import HolographicService
from cloud.app.services.memory_episodic_writer import EpisodicMemoryWriter
from cloud.app.services.memory_procedural_writer import ProceduralMemoryWriter
from cloud.app.services.memory_working_writer import WorkingMemoryWriter


class MemoryWriter(BaseService):
    """记忆写入服务，按写入类型委托到工作、情景与程序记忆组件。"""

    def __init__(self, db, holographic_service=None, holographic_service_factory=None):
        super().__init__(db)
        self._holographic_service = holographic_service
        self._holographic_service_factory = holographic_service_factory
        self._working_writer = WorkingMemoryWriter(self.db)
        self._episodic_writer = EpisodicMemoryWriter(self.db, self._auto_associate)
        self._procedural_writer = ProceduralMemoryWriter(self.db, self._auto_associate)

    @property
    def holographic_service(self):
        if self._holographic_service is None:
            factory = self._holographic_service_factory or HolographicService
            self._holographic_service = factory(self.db)
        return self._holographic_service

    def working_set(
        self,
        session_id: str,
        slot_key: str,
        slot_value: str,
        slot_type: str,
        ttl_seconds: int,
    ) -> dict:
        return self._working_writer.working_set(session_id, slot_key, slot_value, slot_type, ttl_seconds)

    def working_clear(self, session_id: str) -> str:
        return self._working_writer.working_clear(session_id)

    def working_refresh(self, session_id: str) -> dict:
        return self._working_writer.working_refresh(session_id)

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
        return self._episodic_writer.episodic_store(
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

    def episodic_consolidate(self, memory_id: int, auth_header: str) -> dict:
        return self._episodic_writer.episodic_consolidate(memory_id, auth_header)

    def semantic_abstract(
        self,
        source_type: str,
        source_id: str,
        abstraction_level: str,
        auth_header: str = "",
    ) -> dict:
        return self._episodic_writer.semantic_abstract(source_type, source_id, abstraction_level, auth_header)

    def procedural_learn(
        self,
        pattern_name: str,
        trigger_conditions: str,
        action_sequence: str,
        success_rate: float,
    ) -> dict:
        return self._procedural_writer.procedural_learn(pattern_name, trigger_conditions, action_sequence, success_rate)

    def memory_decay(self, hours_threshold: int = 72) -> dict:
        return self._procedural_writer.memory_decay(hours_threshold)

    def _auto_associate(self, entry_id: int, entry: dict):
        self.holographic_service.auto_associate(entry_id, entry)
