"""MDT解析服务，负责多学科团队辩论结果的共识分析与决策。"""

import json
import urllib.request
from datetime import datetime

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    MdtOpinionsRepository,
    MdtParticipantsRepository,
    MdtSessionsRepository,
)
from cloud.app.services.base import BaseService
from shared.base import success
from shared.config import settings as config_settings


class MdtResolver(BaseService):
    """MDT解析服务，提供观点汇总、共识分析与决策生成功能。"""

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _call_ai(messages: list[dict], auth_header: str) -> dict:
        with urllib.request.urlopen(
            urllib.request.Request(
                f"{config_settings.ai_chat_url}",
                data=json.dumps({"messages": messages, "temperature": 0.7, "max_tokens": 2048}).encode("utf-8"),
                headers={"Content-Type": "application/json", "Authorization": auth_header},
                method="POST",
            ),
            timeout=120,
        ) as rp:
            return json.loads(rp.read().decode("utf-8")).get("data", {})

    @staticmethod
    def _parse_json(raw: str, default=None):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return default if default is not None else raw

    def consensus(self, session_id: int, auth_header: str) -> dict:
        """consensus 操作。

        Args:
            session_id: 描述
            auth_header: 描述

        Returns:
            描述
        """
        sessions_repo = MdtSessionsRepository(self.db)
        opinions_repo = MdtOpinionsRepository(self.db)
        s = sessions_repo.get_by_id(session_id)
        if not s:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="MDT Session not found")
        if s["status"] == "completed":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Consensus already generated")
        all_ops = opinions_repo.list_by_session_with_participant(session_id)
        if not all_ops:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No opinions to build consensus from")
        opinions_text = "\n".join(f"[Round {o['round_number']}] {o['role_name']}({o.get('stance', 'neutral')}): {o['opinion']}" for o in all_ops)
        sys_msg = '你是一名MDT辩论主持人，负责总结多方观点形成共识。请基于以下各方辩论意见，生成综合共识报告。以JSON格式输出：{"consensus":"综合共识结论","confidence":0.0-1.0,"agreements":["各方一致认同的点"],"disagreements":["存在分歧的点"],"action_items":["建议下一步行动"]}'
        user_msg = f"议题：{s['title']}\n问题：{s['question']}\n背景：{s['context']}\n\n各方观点：\n{opinions_text}"
        try:
            ai = self._call_ai(
                [{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}],
                auth_header,
            )
            reply = ai.get("reply", "")
            parsed = self._parse_json(reply, {})
            if isinstance(parsed, dict):
                consensus_text = parsed.get("consensus", reply)
                consensus_json = json.dumps(parsed, ensure_ascii=False)
            else:
                consensus_text = reply
                consensus_json = json.dumps({"consensus": reply}, ensure_ascii=False)
            sessions_repo.update_fields(
                session_id,
                {
                    "consensus": consensus_text,
                    "consensus_json": consensus_json,
                    "status": "completed",
                    "updated_at": self._now(),
                },
            )
        except Exception:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail="Failed to generate consensus")
        return success({"consensus": consensus_text, "consensus_json": self._parse_json(consensus_json, {})})

    def dashboard(self) -> dict:
        """dashboard 操作。

        Returns:
            描述
        """
        sessions_repo = MdtSessionsRepository(self.db)
        participants_repo = MdtParticipantsRepository(self.db)
        opinions_repo = MdtOpinionsRepository(self.db)
        total = sessions_repo.count()
        completed = sessions_repo.count_completed()
        by_status = sessions_repo.count_by_field("status")
        avg_parts = participants_repo.avg_per_session()
        avg_rounds = sessions_repo.avg_field("round_count")
        avg_confidence = opinions_repo.avg_confidence()
        recent = sessions_repo.list_recent(limit=5)
        return success(
            {
                "total_sessions": total,
                "completed_sessions": completed,
                "by_status": by_status,
                "avg_participants": avg_parts,
                "avg_rounds": avg_rounds,
                "avg_consensus_confidence": avg_confidence,
                "recent_5": recent,
            }
        )
