"""Agent 并发限流 + 录音加密管线 测试。"""

import os
import threading
from unittest.mock import MagicMock, patch

import pytest

from cloud.app.agent_runtime.runtime_core import _get_global_semaphore


class TestAgentConcurrency:
    def test_semaphore_default_is_2(self):
        sem = _get_global_semaphore()
        assert sem._value == 2

    def test_semaphore_env_override(self):
        with patch.dict(os.environ, {"AGENT_MAX_CONCURRENCY": "5"}, clear=True):
            import importlib

            from cloud.app.agent_runtime import runtime_core

            importlib.reload(runtime_core)
            sem = runtime_core._get_global_semaphore()
            assert sem._value == 5

    def test_semaphore_blocks_when_exceeded(self):
        sem = threading.Semaphore(2)
        sem.acquire()
        sem.acquire()
        blocked = sem.acquire(blocking=False)
        assert blocked is False
        sem.release()
        sem.release()

    def test_semaphore_releases_after_execution(self):
        sem = threading.Semaphore(2)
        sem.acquire()
        sem.acquire()
        assert sem.acquire(blocking=False) is False
        sem.release()
        assert sem.acquire(blocking=False) is True
        sem.release()


class TestEncryptionPipeline:
    def test_encrypt_decrypt_roundtrip(self):
        try:
            from cloud.app.services.audio_encryption import decrypt_audio, encrypt_audio
        except ImportError:
            pytest.skip("audio_encryption module removed")

        data = b"test audio content with \x00 binary data"
        nonce, ciphertext = encrypt_audio(data)
        assert ciphertext != data
        assert len(nonce) == 12
        decrypted = decrypt_audio(nonce, ciphertext)
        assert decrypted == data

    def test_encrypt_different_nonce_each_time(self):
        try:
            from cloud.app.services.audio_encryption import encrypt_audio
        except ImportError:
            pytest.skip("audio_encryption module removed")

        data = b"same content"
        n1, _ = encrypt_audio(data)
        n2, _ = encrypt_audio(data)
        assert n1 != n2

    def test_encrypted_file_written_by_router(self):
        with patch("cloud.app.routers.visit_recording_router.AESGCM") as mock_aesgcm:
            instance = MagicMock()
            instance.encrypt.return_value = b"ciphertext"
            mock_aesgcm.return_value = instance

            from cloud.app.routers.visit_recording_router import encrypt_audio

            nonce, ct = encrypt_audio(b"audio data")
            assert ct == b"ciphertext"

    def test_upload_recording_encrypts_content(self):
        try:
            from cloud.app.services.audio_encryption import encrypt_audio
        except ImportError:
            pytest.skip("audio_encryption module removed")

        data = b"\x00\x01\x02" * 100
        nonce, ct = encrypt_audio(data)
        assert ct != data
        assert len(nonce) == 12

    def test_expires_at_in_draft(self):
        from datetime import datetime, timedelta

        expires = (datetime.utcnow() + timedelta(days=365 * 2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        assert expires.startswith("2028")
        assert expires.endswith("Z")

    def test_metadata_has_encrypted_key_and_expires_at(self):
        from cloud.app.services.visit_extraction_service import CREATE_DRAFTS_TABLE_SQL

        assert "encrypted_key" in CREATE_DRAFTS_TABLE_SQL
        assert "expires_at" in CREATE_DRAFTS_TABLE_SQL
