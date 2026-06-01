import hashlib
import json
import logging
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

import aiofiles
from edge_tts import Communicate

from assistant.app.repositories import MediaFileRepository
from assistant.app.services.base import BaseService

logger = logging.getLogger(__name__)

AI_GATEWAY_URL = "http://localhost:8000/ai/chat"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIO_DIR = os.path.join(BASE_DIR, "uploads", "audio")
TTS_DIR = os.path.join(BASE_DIR, "media", "tts")

for d in (AUDIO_DIR, TTS_DIR):
    os.makedirs(d, exist_ok=True)


class VoiceService(BaseService):
    async def upload(self, file, user_id: int) -> dict:
        ts = int(time.time() * 1000)
        filename = f"{ts}_{file.filename}"
        filepath = os.path.join(AUDIO_DIR, filename)
        content = await file.read()
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)
        now = datetime.now(timezone.utc).isoformat()
        repo = MediaFileRepository(self.db)
        file_id = repo.create(
            {
                "file_type": "audio",
                "original_name": file.filename,
                "storage_path": filepath,
                "mime_type": file.content_type or "audio/mpeg",
                "file_size": len(content),
                "created_by": user_id,
                "created_at": now,
            }
        )
        return {
            "file_id": file_id,
            "original_name": file.filename,
            "file_size": len(content),
            "transcript": "",
        }

    async def chat(self, file, context, auth_header: str, user_id: int) -> dict:
        ts = int(time.time() * 1000)
        filename = f"{ts}_{file.filename}"
        filepath = os.path.join(AUDIO_DIR, filename)
        content = await file.read()
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)
        now = datetime.now(timezone.utc).isoformat()
        repo = MediaFileRepository(self.db)
        file_id = repo.create(
            {
                "file_type": "audio",
                "original_name": file.filename,
                "storage_path": filepath,
                "mime_type": file.content_type or "audio/mpeg",
                "file_size": len(content),
                "created_by": user_id,
                "created_at": now,
            }
        )

        prompt = context or "用户发送了一段语音，请以专业临床药师的身份回复。"
        reply = ""
        try:
            reply = self._call_llm(auth_header, prompt)
        except Exception as e:
            logger.warning("AI call failed: %s", e)
            reply = "抱歉，AI服务暂时不可用。"

        repo.update(
            file_id,
            {
                "transcript": prompt,
                "analysis_result": reply,
            },
        )

        tts_path = os.path.join(TTS_DIR, f"{file_id}.mp3")
        audio_url = ""
        try:
            comm = Communicate(text=reply, voice="zh-CN-XiaoxiaoNeural")
            await comm.save(tts_path)
            audio_url = f"/media/tts/{file_id}.mp3"
        except Exception as e:
            logger.warning("TTS failed: %s", e)

        return {
            "text_reply": reply,
            "audio_url": audio_url,
            "file_id": file_id,
        }

    async def synthesize(self, text: str, voice: str) -> str:
        hash_key = hashlib.md5(f"{text.strip()}:{voice}".encode()).hexdigest()
        tts_path = os.path.join(TTS_DIR, f"{hash_key}.mp3")
        if not os.path.exists(tts_path):
            comm = Communicate(text=text.strip(), voice=voice)
            await comm.save(tts_path)
        return tts_path

    def get_audio(self, file_id: int) -> dict:
        repo = MediaFileRepository(self.db)
        row = repo.get_by_id(file_id)
        if not row or not row["is_active"]:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Audio not found")
        return dict(row)

    def _call_llm(self, auth_header: str, prompt: str) -> str:
        req_body = {
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位资深临床药师，请以专业的角度回答问题。",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 2048,
        }
        req = urllib.request.Request(
            AI_GATEWAY_URL,
            data=json.dumps(req_body).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": auth_header},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read()).get("data", {}).get("reply", "")
