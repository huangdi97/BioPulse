"""
ASR (Automatic Speech Recognition) service stub.

This module is ready for integration with iFlytek or Alibaba Cloud ASR APIs.
Replace the stub implementation with real API calls once ASR_PROVIDER and
ASR_API_KEY are configured in .env.
"""

import logging
import os

logger = logging.getLogger(__name__)


async def transcribe_audio(file_path: str) -> dict:
    """
    Transcribe an audio file to text using a configured ASR provider.

    Args:
        file_path: Absolute or relative path to the audio file.

    Returns:
        A dictionary with:
            - text (str):       Full transcribed text.
            - confidence (float): Overall confidence score (0-1).
            - segments (list):  List of per-segment dicts, each containing:
                - start (float): Start time in seconds.
                - end (float):   End time in seconds.
                - text (str):    Transcribed text for the segment.

    Raises:
        FileNotFoundError: If the audio file does not exist.
        NotImplementedError: If no ASR API key is configured.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    logger.info("ASR transcription attempt for: %s", file_path)

    provider = os.getenv("ASR_PROVIDER")
    api_key = os.getenv("ASR_API_KEY")

    if not provider or not api_key:
        raise NotImplementedError("ASR API not configured - set ASR_PROVIDER and ASR_API_KEY in .env")

    # TODO: Replace with real provider integration (iFlytek / Alibaba ASR).
    # Expected response shape:
    # {
    #     "text": "...",
    #     "confidence": 0.95,
    #     "segments": [
    #         {"start": 0.0, "end": 2.5, "text": "..."},
    #         ...
    #     ],
    # }
    raise NotImplementedError(f"ASR provider '{provider}' integration is not yet implemented")
