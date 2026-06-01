import json
import logging
import urllib.error
import urllib.request
from typing import Any

from sales_assistant.app.repositories import HcpRepository, ScheduleRepository, VisitRepository
from sales_assistant.app.services.base import BaseService

AI_GATEWAY_URL = "http://localhost:8000/ai/chat"
TIMEOUT_SECONDS = 30
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是一位资深的医药销售顾问，拥有丰富的临床知识和行业经验。"
    "请根据客户信息生成一份专业的拜访简报。回复必须严格使用以下JSON格式："
    '{"basic_info":"...","prescription_tendency":"...","recent_research":"...",'
    '"history_summary":"...","talking_points":["...","..."],"suggested_approach":"..."}'
)


class PrecallService(BaseService):
    def _build_user_message(self, body, db_context: str = "") -> str:
        parts = [f"客户姓名：{body.customer_name}"]
        if body.hospital:
            parts.append(f"所属医院：{body.hospital}")
        if db_context:
            parts.append(f"数据库记录：\n{db_context}")
        if body.extra_context:
            parts.append(f"额外信息：{body.extra_context}")
        parts.append("请生成拜访简报。")
        return "\n".join(parts)

    def _build_fallback_brief(self, body) -> dict:
        hospital_text = body.hospital or "未知医院"
        return {
            "basic_info": f"{body.customer_name}就职于{hospital_text}，具体科室信息待补充。",
            "prescription_tendency": "处方偏好暂无法获取，建议拜访时重点关注。",
            "recent_research": "近期研究动态待确认。",
            "history_summary": "暂无历史拜访记录。",
            "talking_points": [
                "介绍公司最新产品信息",
                "了解客户当前处方习惯和需求",
                "探讨学术合作机会",
            ],
            "suggested_approach": "以学术交流为主，建立专业信任关系，先了解客户实际需求再推荐产品。",
        }

    def _gather_db_context(self, customer_name: str, hospital: str | None = None) -> str:
        parts: list[str] = []
        hcp_repo = HcpRepository(self.db)
        visit_repo = VisitRepository(self.db)
        schedule_repo = ScheduleRepository(self.db)

        hcp_rows = hcp_repo.search(customer_name, limit=5)
        if hospital:
            hcp_rows = [r for r in hcp_rows if r["hospital"] == hospital]
        if hcp_rows:
            hcp = hcp_rows[0]
            parts.append(
                f"HCP信息：姓名={hcp['name']}，医院={hcp['hospital']}，"
                f"科室={hcp['department']}，职称={hcp['specialty']}，等级={hcp['tier']}"
            )

            visits = visit_repo.search(customer_name, limit=5)
            if visits:
                visit_lines = []
                for v in visits:
                    visit_lines.append(
                        f"- 产品:{v['products_discussed']} 反馈:{v['hcp_feedback']}"
                    )
                parts.append("近期拜访记录：\n" + "\n".join(visit_lines))

            schedules = schedule_repo.search(customer_name, limit=5)
            if schedules:
                sched_lines = []
                for s in schedules:
                    sched_lines.append(
                        f"- {s['title']} @ {s['location']} ({s['start_time']})"
                    )
                parts.append("相关日程：\n" + "\n".join(sched_lines))

        return "\n".join(parts)

    def _call_ai_gateway(self, auth_header: str, body, db_context: str = "") -> dict[str, Any]:
        req_body = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": self._build_user_message(body, db_context)},
            ],
            "temperature": 0.7,
            "max_tokens": 2048,
        }
        req_data = json.dumps(req_body).encode("utf-8")
        req = urllib.request.Request(
            AI_GATEWAY_URL,
            data=req_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": auth_header,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            raw = resp.read()
        envelope = json.loads(raw)
        return envelope.get("data", {})

    def _parse_brief(self, raw_reply: str, body) -> dict:
        try:
            parsed = json.loads(raw_reply)
            return {
                "basic_info": parsed.get("basic_info", ""),
                "prescription_tendency": parsed.get("prescription_tendency", ""),
                "recent_research": parsed.get("recent_research", ""),
                "history_summary": parsed.get("history_summary", ""),
                "talking_points": parsed.get("talking_points", []),
                "suggested_approach": parsed.get("suggested_approach", ""),
            }
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("Failed to parse AI brief JSON: %s, using fallback", exc)
            return self._build_fallback_brief(body)

    def precall(self, body, auth_header: str = "") -> dict:
        db_context = self._gather_db_context(body.customer_name, body.hospital)
        try:
            ai_data = self._call_ai_gateway(auth_header, body, db_context)
            reply = ai_data.get("reply", "")
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            logger.warning("AI gateway unavailable: %s, using fallback", exc)
            reply = ""
        except Exception:
            logger.exception("Unexpected error calling AI gateway")
            reply = ""

        brief = self._parse_brief(reply, body) if reply else self._build_fallback_brief(body)
        return {
            "customer_name": body.customer_name,
            "hospital": body.hospital,
            "brief": brief,
        }
