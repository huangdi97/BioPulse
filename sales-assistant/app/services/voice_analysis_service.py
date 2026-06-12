"""录音转文字与拜访摘要服务。"""

import json
import logging
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, HTTPException, UploadFile
from starlette import status

from sales_assistant.app.database import get_db
from sales_assistant.app.schemas.voice_analysis import VoiceAnalysisResult
from shared.ai_gateway import TIMEOUT_SECONDS
from shared.app_settings import settings

AI_GATEWAY_URL = f"{settings.cloud_api_base}/ai/chat"
logger = logging.getLogger(__name__)


class VoiceAnalysisService:
    """处理录音上传、ASR占位转写、LLM结构化摘要与结果持久化。"""

    def __init__(self, db=Depends(get_db)):
        self.db = db

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _pk_sql(self) -> str:
        return "SERIAL PRIMARY KEY" if self.db.__class__.__name__ == "PGCompatConnection" else "INTEGER PRIMARY KEY AUTOINCREMENT"

    def _ensure_table(self) -> None:
        self.db.execute(
            f"""
            CREATE TABLE IF NOT EXISTS voice_analysis (
                id {self._pk_sql()},
                visit_id TEXT NOT NULL UNIQUE,
                hcp_id TEXT,
                file_path TEXT NOT NULL,
                transcript TEXT,
                summary TEXT,
                key_points TEXT,
                concerns TEXT,
                commitments TEXT,
                next_steps TEXT,
                sentiment TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        self.db.commit()

    def save_upload(self, file: UploadFile, visit_id: str) -> str:
        """保存上传录音文件并返回本地路径。"""
        safe_visit_id = "".join(ch for ch in visit_id if ch.isalnum() or ch in ("-", "_")) or "visit"
        safe_name = os.path.basename(file.filename or "recording.wav")
        upload_dir = os.path.join(os.getcwd(), "data", "uploads", "voice")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{safe_visit_id}-{int(datetime.now().timestamp())}-{safe_name}")
        content = file.file.read()
        with open(file_path, "wb") as fh:
            fh.write(content)
        return file_path

    def _transcribe_audio(self, file_path: str) -> str:
        """ASR适配点：当前返回可追溯的占位转写，便于后续替换真实ASR。"""
        size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        return f"录音文件已接收：{os.path.basename(file_path)}，大小 {size} 字节。请结合拜访记录补充真实转写。"

    def _fallback_analysis(self, transcript: str) -> VoiceAnalysisResult:
        return VoiceAnalysisResult(
            transcript=transcript,
            summary="已完成录音接收，ASR/LLM网关不可用时生成基础摘要。",
            key_points=["记录本次拜访沟通内容", "后续可接入ASR服务生成完整转写"],
            concerns=[],
            commitments=[],
            next_steps=["复核录音内容", "补充HCP关注点与下一步行动"],
            sentiment="neutral",
        )

    def _call_llm(self, transcript: str) -> VoiceAnalysisResult:
        prompt = (
            "你是医药代表拜访记录分析助手。请从录音转写中提取结构化摘要，"
            "严格回复JSON："
            '{"summary":"...","key_points":["..."],"concerns":["..."],'
            '"commitments":["..."],"next_steps":["..."],"sentiment":"positive|neutral|negative"}'
        )
        req = urllib.request.Request(
            AI_GATEWAY_URL,
            data=json.dumps(
                {
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": transcript},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1200,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            reply = json.loads(resp.read()).get("data", {}).get("reply", "")
        parsed: dict[str, Any] = json.loads(reply) if reply else {}
        return VoiceAnalysisResult(
            transcript=transcript,
            summary=parsed.get("summary", ""),
            key_points=parsed.get("key_points", []),
            concerns=parsed.get("concerns", []),
            commitments=parsed.get("commitments", []),
            next_steps=parsed.get("next_steps", []),
            sentiment=parsed.get("sentiment", "neutral"),
        )

    def _update_visit_summary(self, visit_id: str, summary: str) -> None:
        if not visit_id.isdigit():
            return
        row = self.db.execute("SELECT id FROM schedule WHERE id = ?", (int(visit_id),)).fetchone()
        if not row:
            return
        self.db.execute(
            "UPDATE schedule SET description = ?, updated_at = ? WHERE id = ?",
            (summary, self._now(), int(visit_id)),
        )

    def _store_result(
        self,
        file_path: str,
        visit_id: str,
        hcp_id: str | None,
        result: VoiceAnalysisResult,
    ) -> None:
        self._ensure_table()
        now = self._now()
        payload = (
            visit_id,
            hcp_id,
            file_path,
            result.transcript,
            result.summary,
            json.dumps(result.key_points, ensure_ascii=False),
            json.dumps(result.concerns, ensure_ascii=False),
            json.dumps(result.commitments, ensure_ascii=False),
            json.dumps(result.next_steps, ensure_ascii=False),
            result.sentiment,
            now,
            now,
        )
        self.db.execute(
            """
            INSERT INTO voice_analysis (
                visit_id, hcp_id, file_path, transcript, summary, key_points,
                concerns, commitments, next_steps, sentiment, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(visit_id) DO UPDATE SET
                hcp_id = excluded.hcp_id,
                file_path = excluded.file_path,
                transcript = excluded.transcript,
                summary = excluded.summary,
                key_points = excluded.key_points,
                concerns = excluded.concerns,
                commitments = excluded.commitments,
                next_steps = excluded.next_steps,
                sentiment = excluded.sentiment,
                updated_at = excluded.updated_at
            """,
            payload,
        )
        self._update_visit_summary(visit_id, result.summary)
        self.db.commit()

    def process_audio(self, file_path: str, visit_id: str, hcp_id: str | None = None) -> VoiceAnalysisResult:
        """接收音频文件，生成转写和AI摘要，并更新拜访摘要。"""
        if not os.path.exists(file_path):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found")
        transcript = self._transcribe_audio(file_path)
        try:
            result = self._call_llm(transcript)
            if not result.summary:
                result = self._fallback_analysis(transcript)
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, ValueError) as exc:
            logger.warning("Voice AI analysis fallback: %s", exc)
            result = self._fallback_analysis(transcript)
        except Exception:
            logger.exception("Unexpected voice analysis error")
            result = self._fallback_analysis(transcript)
        self._store_result(file_path, visit_id, hcp_id, result)
        return result

    def get_analysis(self, visit_id: str) -> dict:
        """按 visit_id 查询录音分析结果。"""
        self._ensure_table()
        row = self.db.execute("SELECT * FROM voice_analysis WHERE visit_id = ?", (visit_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice analysis not found")
        data = dict(row)
        for field in ("key_points", "concerns", "commitments", "next_steps"):
            data[field] = json.loads(data.get(field) or "[]")
        return data
