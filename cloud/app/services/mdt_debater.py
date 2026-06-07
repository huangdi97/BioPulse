"""MDT辩论服务，负责多学科团队辩论会话的管理与AI辩论编排。"""

import json
import urllib.request
from datetime import datetime

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    AgentRolesRepository,
    MdtOpinionsRepository,
    MdtParticipantsRepository,
    MdtSessionsRepository,
)
from cloud.app.services.base import BaseService
from shared.base import success
from shared.config import settings as config_settings


class MdtDebater(BaseService):
    """MDT辩论服务，提供辩论会话的创建、管理、发言与AI辩论功能。"""

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

    def create_session(self, body, uid: int) -> dict:
        """创建会话。

        Args:
            uid: 描述

        Returns:
            描述
        """
        n = self._now()
        sessions_repo = MdtSessionsRepository(self.db)
        participants_repo = MdtParticipantsRepository(self.db)
        roles_repo = AgentRolesRepository(self.db)
        sid = sessions_repo.create(
            {
                "title": body.title,
                "question": body.question,
                "context": body.context,
                "status": "active",
                "created_by": uid,
                "created_at": n,
                "updated_at": n,
            }
        )
        parts = body.participants
        if not parts:
            from cloud.app.mdt_engine_router import ParticipantDef

            roles = roles_repo.list_active(limit=5)
            parts = [ParticipantDef(agent_role_id=r["id"], role_name=r["name"], stance="neutral", vote_weight=1.0) for r in roles]
        for p in parts:
            participants_repo.create_raw(
                {
                    "session_id": sid,
                    "agent_role_id": p.agent_role_id,
                    "role_name": p.role_name,
                    "stance": p.stance,
                    "vote_weight": p.vote_weight,
                    "created_at": n,
                }
            )
        return success({"id": sid, "title": body.title, "participant_count": len(parts)})

    def list_sessions(self, status_filter, page: int, page_size: int) -> dict:
        """获取会话列表。

        Args:
            status_filter: 描述
            page: 描述
            page_size: 描述

        Returns:
            描述
        """
        sessions_repo = MdtSessionsRepository(self.db)
        conditions, params = [], []
        if status_filter:
            conditions.append("status=?")
            params.append(status_filter)
        total, total_pages, items = sessions_repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )
        return success({"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages})

    def get_session(self, session_id: int) -> dict:
        """获取会话。

        Args:
            session_id: 描述

        Returns:
            描述
        """
        sessions_repo = MdtSessionsRepository(self.db)
        participants_repo = MdtParticipantsRepository(self.db)
        opinions_repo = MdtOpinionsRepository(self.db)
        s = sessions_repo.get_by_id(session_id)
        if not s:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="MDT Session not found")
        parts = participants_repo.list_by_session(session_id)
        opinions = opinions_repo.list_by_session(session_id)
        return success({"session": s, "participants": parts, "opinions": opinions})

    def debate(self, session_id: int, max_rounds: int, auth_header: str) -> dict:
        """debate 操作。

        Args:
            session_id: 描述
            max_rounds: 描述
            auth_header: 描述

        Returns:
            描述
        """
        sessions_repo = MdtSessionsRepository(self.db)
        participants_repo = MdtParticipantsRepository(self.db)
        opinions_repo = MdtOpinionsRepository(self.db)
        roles_repo = AgentRolesRepository(self.db)
        s = sessions_repo.get_by_id(session_id)
        if not s:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="MDT Session not found")
        if s["status"] == "completed":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Session already completed")
        participants = participants_repo.list_by_session(session_id)
        if not participants:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No participants in session")
        current_round = s["round_count"] or 0
        results = []
        for _ in range(max_rounds):
            current_round += 1
            prev = opinions_repo.build_round_summary(session_id, current_round - 1)
            for p in participants:
                role = roles_repo.get_system_prompt(p["agent_role_id"])
                if not role:
                    continue
                json_fmt = '\n\n请以JSON格式输出你的观点：{"opinion":"你的详细观点","summary":"一句话总结","sentiment":"positive/negative/neutral/constructive/mixed/analytical","confidence":0.0-1.0,"key_points":["要点1","要点2"]}'
                sys_msg = role["system_prompt"] + json_fmt
                user_msg = f"问题：{s['question']}\n背景：{s['context']}"
                if prev:
                    user_msg += f"\n\n上一轮各方观点摘要：\n{prev}"
                try:
                    ai = self._call_ai([{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}], auth_header)
                    reply = ai.get("reply", "")
                    parsed = self._parse_json(reply, {})
                    if isinstance(parsed, dict):
                        opinion = parsed.get("opinion", reply)
                        summary = parsed.get("summary", "")
                        sentiment = parsed.get("sentiment", "neutral")
                        confidence = float(parsed.get("confidence", 0.5))
                        key_points = json.dumps(parsed.get("key_points", []), ensure_ascii=False)
                    else:
                        opinion = reply
                        summary = ""
                        sentiment = "neutral"
                        confidence = 0.5
                        key_points = "[]"
                    opinions_repo.create_raw(
                        {
                            "session_id": session_id,
                            "participant_id": p["id"],
                            "round_number": current_round,
                            "opinion": opinion,
                            "summary": summary,
                            "sentiment": sentiment,
                            "confidence": confidence,
                            "key_points": key_points,
                            "ai_response_raw": reply,
                            "tokens_used": ai.get("usage", {}).get("total_tokens", 0),
                            "created_at": self._now(),
                        }
                    )
                    results.append(
                        {
                            "participant_id": p["id"],
                            "round": current_round,
                            "sentiment": sentiment,
                            "confidence": confidence,
                        }
                    )
                except Exception:
                    results.append({"participant_id": p["id"], "round": current_round, "error": "AI call failed"})
        sessions_repo.update_fields(session_id, {"round_count": current_round, "updated_at": self._now()})
        return success({"round": current_round, "results": results})

    def get_opinions(self, session_id: int, round_number: int | None = None) -> dict:
        """get_opinions 操作。

        Args:
            session_id: 描述
            round_number: 描述

        Returns:
            描述
        """
        sessions_repo = MdtSessionsRepository(self.db)
        opinions_repo = MdtOpinionsRepository(self.db)
        s = sessions_repo.get_by_id(session_id)
        if not s:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="MDT Session not found")
        rows = opinions_repo.list_by_session_with_participant(session_id)
        if round_number is not None:
            rows = [r for r in rows if r.get("round_number") == round_number]
        return success(rows)

    def timeline(self, session_id: int) -> dict:
        """timeline 操作。

        Args:
            session_id: 描述

        Returns:
            描述
        """
        sessions_repo = MdtSessionsRepository(self.db)
        opinions_repo = MdtOpinionsRepository(self.db)
        s = sessions_repo.get_by_id(session_id)
        if not s:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="MDT Session not found")
        opinions = opinions_repo.list_by_session_with_participant(session_id)
        rounds: dict = {}
        for o in opinions:
            rn = str(o["round_number"])
            rounds.setdefault(rn, []).append(o)
        timeline_data = {
            "session": s,
            "rounds": [{"round_number": int(k), "opinions": v} for k, v in sorted(rounds.items(), key=lambda x: int(x[0]))],
        }
        if s["status"] == "completed" and s.get("consensus"):
            timeline_data["consensus"] = {
                "text": s["consensus"],
                "detail": self._parse_json(s.get("consensus_json"), {}),
                "updated_at": s["updated_at"],
            }
        return success(timeline_data)
