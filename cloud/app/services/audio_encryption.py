import logging
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

_KEY: bytes | None = None


def _get_key() -> bytes:
    global _KEY
    if _KEY is not None:
        return _KEY
    raw = os.getenv("RECORDING_ENCRYPTION_KEY", "")
    if raw:
        _KEY = bytes.fromhex(raw) if len(raw) == 64 else raw.encode()[:32].ljust(32, b"\0")
    else:
        _KEY = os.urandom(32)
    if len(_KEY) != 32:
        _KEY = _KEY[:32].ljust(32, b"\0")
    return _KEY


def encrypt_audio(data: bytes) -> tuple[bytes, bytes]:
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return nonce, ciphertext


def decrypt_audio(nonce: bytes, ciphertext: bytes) -> bytes:
    key = _get_key()
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)
