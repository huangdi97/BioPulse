"""Tests for LLM structured field extraction pipeline."""

from __future__ import annotations

import json

import pytest

from cloud.app.config.provider_config import ProviderSettings
from cloud.app.services.extraction_schema import ExtractionSchema
from cloud.app.services.llm_extraction_service import (
    LLMExtractionError,
    LLMExtractionService,
    SchemaValidationError,
)
from cloud.app.services.llm_service import LlmService
from cloud.app.services.memory_service import MemoryService


class FakeLLM:
    def __init__(self, responses: list[str] | None = None) -> None:
        self._responses = responses or []
        self._call_count = 0

    async def generate(self, prompt: str, context: str | None = None) -> str:
        if self._call_count < len(self._responses):
            resp = self._responses[self._call_count]
            self._call_count += 1
            return resp
        return json.dumps({"doctor_name": "Dr. Li", "key_points": ["discussed dosage"], "action": "follow up"})

    def switch_mode(self, mode) -> None:
        pass


class TestExtractionSchema:
    def test_valid_string_type(self) -> None:
        s = ExtractionSchema(field_name="doctor_name", description="Doctor's name", type="string")
        assert s.field_name == "doctor_name"

    def test_valid_enum_with_options(self) -> None:
        s = ExtractionSchema(field_name="action", description="Next action", type="enum", enum_options=["follow_up", "prescription", "none"])
        assert s.enum_options == ["follow_up", "prescription", "none"]

    def test_invalid_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid type"):
            ExtractionSchema(field_name="x", description="x", type="float")

    def test_enum_options_on_non_enum_raises(self) -> None:
        with pytest.raises(ValueError, match="enum_options only allowed"):
            ExtractionSchema(field_name="x", description="x", type="string", enum_options=["a", "b"])


class TestLLMExtractionService:
    @pytest.mark.asyncio
    async def test_extract_returns_structured_dict(self) -> None:
        llm = FakeLLM()
        mem = MemoryService()
        svc = LLMExtractionService(llm, mem)
        schema = ExtractionSchema(field_name="doctor_name", description="Doctor name", type="string")
        result = await svc.extract_structured_fields("Dr. Li prescribed Atorvastatin", schema)
        assert "doctor_name" in result
        assert result["doctor_name"] == "Dr. Li"

    @pytest.mark.asyncio
    async def test_extract_stores_in_memory(self) -> None:
        llm = FakeLLM()
        mem = MemoryService()
        svc = LLMExtractionService(llm, mem)
        schema = ExtractionSchema(field_name="doctor_name", description="Doctor name", type="string")
        await svc.extract_structured_fields("Dr. Li", schema)
        namespace = mem.get_namespace("visit_extraction")
        stored = namespace.retrieve("doctor_name")
        assert stored is not None
        parsed = json.loads(stored)
        assert parsed["doctor_name"] == "Dr. Li"

    @pytest.mark.asyncio
    async def test_missing_required_field_raises(self) -> None:
        llm = FakeLLM(responses=[json.dumps({"wrong_key": "value"})])
        mem = MemoryService()
        svc = LLMExtractionService(llm, mem)
        schema = ExtractionSchema(field_name="doctor_name", description="Doctor name", type="string")
        with pytest.raises(SchemaValidationError, match="Required field 'doctor_name' missing"):
            await svc.extract_structured_fields("Dr. Li", schema)

    @pytest.mark.asyncio
    async def test_invalid_json_raises(self) -> None:
        llm = FakeLLM(responses=["not valid json"])
        mem = MemoryService()
        svc = LLMExtractionService(llm, mem)
        schema = ExtractionSchema(field_name="doctor_name", description="Doctor name", type="string")
        with pytest.raises(LLMExtractionError, match="not valid JSON"):
            await svc.extract_structured_fields("Dr. Li", schema)

    @pytest.mark.asyncio
    async def test_uses_provider_from_llm_service(self) -> None:
        settings = ProviderSettings(service="llm", enabled=True)
        llm = LlmService(provider_settings=settings)
        mem = MemoryService()
        svc = LLMExtractionService(llm, mem)
        assert svc._llm is llm
        assert svc._llm.settings.enabled is True

    @pytest.mark.asyncio
    async def test_extract_enum_field(self) -> None:
        llm = FakeLLM(responses=[json.dumps({"action": "follow_up"})])
        mem = MemoryService()
        svc = LLMExtractionService(llm, mem)
        schema = ExtractionSchema(
            field_name="action",
            description="Next action",
            type="enum",
            enum_options=["follow_up", "prescription", "none"],
        )
        result = await svc.extract_structured_fields("schedule next visit in 2 weeks", schema)
        assert result["action"] == "follow_up"
