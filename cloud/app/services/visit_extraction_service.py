"""
Visit extraction service.
Orchestrates ASR transcription and LLM-based structured field extraction
from voice-of-customer visit recordings.
"""

from cloud.app.services.asr_service import transcribe_audio

DEFAULT_CONFIDENCE_THRESHOLD = 0.8


async def extract_visit_fields(transcript: str, confidence: float) -> dict:
    raise NotImplementedError("LLM extraction not configured - requires LLM API access")


async def generate_visit_draft(audio_file: str, user_id: str) -> dict:
    asr_result = await transcribe_audio(audio_file)
    transcript = asr_result["text"]
    confidence = asr_result["confidence"]

    extracted = None
    if confidence > DEFAULT_CONFIDENCE_THRESHOLD:
        extracted = await extract_visit_fields(transcript, confidence)

    return {
        "user_id": user_id,
        "source_audio": audio_file,
        "transcript": transcript,
        "asr_confidence": confidence,
        "extracted_fields": extracted,
    }
