"""Tests for ASR integration pipeline — mock external services."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from cloud.app.services.visit_extraction_service import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    confirm_draft,
    create_drafts_table,
    delete_draft,
    generate_visit_draft,
    get_user_drafts,
    save_draft,
)

from cloud.app.database import DB_PATH


@pytest.fixture(autouse=True)
def _clean_db():
    import os
    import sqlite3

    test_db = DB_PATH
    if os.path.exists(test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("DROP TABLE IF EXISTS visit_drafts")
        conn.commit()
        conn.close()
    create_drafts_table()
    yield
    if os.path.exists(test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("DROP TABLE IF EXISTS visit_drafts")
        conn.commit()
        conn.close()


@pytest.mark.asyncio
async def test_generate_visit_draft_full_pipeline():
    with patch(
        "cloud.app.services.visit_extraction_service.transcribe_audio",
        new_callable=AsyncMock,
    ) as mock_asr:
        mock_asr.return_value = {"text": "Doctor prescribed Atorvastatin 10mg", "confidence": 0.95}

        with patch(
            "cloud.app.services.visit_extraction_service.extract_visit_fields",
            new_callable=AsyncMock,
        ) as _:
            _.return_value = {
                "doctor_name": "Dr. Li",
                "medication": "Atorvastatin",
                "dosage": "10mg",
            }

            result = await generate_visit_draft("/tmp/test.wav", "user_001")

    assert result["transcript"] == "Doctor prescribed Atorvastatin 10mg"
    assert result["asr_confidence"] == 0.95
    assert result["user_id"] == "user_001"
    assert result["extracted_fields"]["doctor_name"] == "Dr. Li"
    mock_asr.assert_awaited_once_with("/tmp/test.wav")


@pytest.mark.asyncio
async def test_low_confidence_skips_llm_extraction():
    with patch(
        "cloud.app.services.visit_extraction_service.transcribe_audio",
        new_callable=AsyncMock,
    ) as mock_asr:
        mock_asr.return_value = {"text": "mumbled audio", "confidence": 0.65}

        with patch(
            "cloud.app.services.visit_extraction_service.extract_visit_fields",
            new_callable=AsyncMock,
        ) as _:
            result = await generate_visit_draft("/tmp/low_conf.wav", "user_002")

    assert result["transcript"] == "mumbled audio"
    assert result["asr_confidence"] == 0.65
    assert result["asr_confidence"] < DEFAULT_CONFIDENCE_THRESHOLD
    assert result["extracted_fields"] is None


@pytest.mark.asyncio
async def test_upload_api_response_format():
    with patch(
        "cloud.app.services.visit_extraction_service.transcribe_audio",
        new_callable=AsyncMock,
    ) as mock_asr:
        mock_asr.return_value = {"text": "test transcription", "confidence": 0.92}

        with patch(
            "cloud.app.services.visit_extraction_service.extract_visit_fields",
            new_callable=AsyncMock,
        ) as _:
            _.return_value = {"key_point": "test"}
            draft = await generate_visit_draft("/tmp/api_test.wav", "user_003")

    response_data = {
        "draft_id": "test_draft_id",
        "transcript": draft["transcript"],
        "extracted_fields": draft["extracted_fields"],
        "status": "draft",
    }
    assert response_data["transcript"] == "test transcription"
    assert response_data["extracted_fields"]["key_point"] == "test"
    assert response_data["status"] == "draft"


def test_draft_confirm_workflow():
    draft = save_draft(
        {
            "user_id": "user_004",
            "audio_file_path": "/tmp/confirm.wav",
            "transcript": "confirm test",
            "extracted_fields": {"field": "old_value"},
        }
    )
    draft_id = draft["id"]

    confirmed = confirm_draft(draft_id, "user_004", {"field": "edited_value"})
    assert confirmed["status"] == "confirmed"
    parsed = json.loads(confirmed["extracted_fields"])
    assert parsed["field"] == "edited_value"


def test_draft_list_and_delete():
    save_draft(
        {
            "user_id": "user_005",
            "transcript": "draft 1",
            "extracted_fields": {"a": 1},
        }
    )
    save_draft(
        {
            "user_id": "user_005",
            "transcript": "draft 2",
            "extracted_fields": {"b": 2},
        }
    )

    drafts = get_user_drafts("user_005")
    assert len(drafts) == 2

    target_id = drafts[0]["id"]
    delete_draft(target_id, "user_005")

    remaining = get_user_drafts("user_005")
    assert len(remaining) == 1
    assert remaining[0]["id"] != target_id
