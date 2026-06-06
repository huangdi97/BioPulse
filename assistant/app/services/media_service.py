"""多媒体服务模块。"""

import json
import logging
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from io import BytesIO

from docx import Document
from PIL import Image
from pypdf import PdfReader

from assistant.app.repositories import MediaFileRepository
from assistant.app.services.base import BaseService

logger = logging.getLogger(__name__)

AI_GATEWAY_URL = "http://localhost:8000/ai/chat"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IMAGE_DIR = os.path.join(BASE_DIR, "uploads", "images")
DOC_DIR = os.path.join(BASE_DIR, "uploads", "documents")

for d in (IMAGE_DIR, DOC_DIR):
    os.makedirs(d, exist_ok=True)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
DOC_EXTS = {".pdf", ".docx"}


class MediaService(BaseService):
    """多媒体服务，提供文件上传、文本提取与AI分析。"""

    async def upload(self, file, user_id: int) -> dict:
        from fastapi import HTTPException

        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in IMAGE_EXTS and ext not in DOC_EXTS:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

        raw = await file.read()
        if ext in IMAGE_EXTS:
            try:
                Image.open(BytesIO(raw)).verify()
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid image file")
            save_dir = IMAGE_DIR
            file_type = "image"
        else:
            save_dir = DOC_DIR
            file_type = "document"

        ts = int(time.time() * 1000)
        filename = f"{ts}_{file.filename}"
        filepath = os.path.join(save_dir, filename)
        with open(filepath, "wb") as f:
            f.write(raw)

        extracted = self._extract_text(filepath, ext) if ext in DOC_EXTS else ""
        now = datetime.now(timezone.utc).isoformat()
        repo = MediaFileRepository(self.db)
        file_id = repo.create(
            data={
                "file_type": file_type,
                "original_name": file.filename,
                "storage_path": filepath,
                "mime_type": file.content_type or "",
                "file_size": len(raw),
                "transcript": extracted,
            },
            extra={"created_by": user_id, "created_at": now},
        )
        return {
            "file_id": file_id,
            "file_type": file_type,
            "original_name": file.filename,
            "extracted_text": extracted,
        }

    def get_media(self, file_id: int) -> dict:
        from fastapi import HTTPException

        repo = MediaFileRepository(self.db)
        row = repo.get_by_id(file_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=404, detail="Media not found")
        return dict(row)

    def analyze(self, file_id: int, auth_header: str) -> dict:
        from fastapi import HTTPException

        repo = MediaFileRepository(self.db)
        row = repo.get_by_id(file_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=404, detail="Media not found")

        context = row["transcript"] or ""
        prompt = f"请分析以下内容并提供专业临床药学的见解。\n\n{context}" if context else "没有可分析的内容"
        analysis = ""
        try:
            analysis = self._call_llm(auth_header, prompt, context)
        except Exception as e:
            logger.warning("AI analysis failed: %s", e)
            analysis = "AI分析服务暂时不可用。"

        repo.update(file_id, {"analysis_result": analysis})
        return {"analysis": analysis, "confidence": "medium"}

    def _extract_text(self, filepath: str, ext: str) -> str:
        if ext == ".pdf":
            reader = PdfReader(filepath)
            return "\n".join(p.extract_text() or "" for p in reader.pages)
        if ext == ".docx":
            doc = Document(filepath)
            return "\n".join(p.text for p in doc.paragraphs)
        return ""

    def _call_llm(self, auth_header: str, prompt: str, context: str = "") -> str:
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        req_body = {
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位资深临床药师，请以专业的角度分析以下内容。",
                },
                {"role": "user", "content": full_prompt},
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
