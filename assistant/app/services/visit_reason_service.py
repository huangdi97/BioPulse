"""拜访理由生成服务。根据HCP画像和业务目标生成拜访理由。"""

import json
import logging

from shared.ai_gateway import call_ai_gateway
from shared.base_service import BaseService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是一位医药销售策略顾问。根据医生画像和业务目标生成3条拜访理由建议。"
    "每条理由需包含：标题、详细说明、建议携带资料。"
    "必须输出严格 JSON 数组格式：\n"
    "[\n"
    "  {\n"
    '    "title": "拜访理由标题",\n'
    '    "detail": "详细说明为什么拜访",\n'
    '    "materials": ["建议携带资料列表"],\n'
    '    "priority": "高/中/低"\n'
    "  }\n"
    "]"
)


class VisitReasonService(BaseService):
    """根据HCP画像和业务目标生成拜访理由。"""

    def generate(self, body, auth_header: str) -> dict:
        try:
            ai_data = self._call_ai_gateway(auth_header, body)
            reply = ai_data.get("reply", "")
        except Exception:
            logger.exception("VisitReason AI gateway call failed")
            return self._build_fallback(body)

        if not reply:
            return self._build_fallback(body)

        return self._parse_reply(reply, body)

    def _build_user_message(self, body) -> str:
        parts = [f"医生姓名：{body.hcp_name}"]
        if body.hospital:
            parts.append(f"医院：{body.hospital}")
        if body.department:
            parts.append(f"科室：{body.department}")
        if body.title:
            parts.append(f"职称：{body.title}")
        if body.product:
            parts.append(f"推广产品：{body.product}")
        if body.last_visit:
            parts.append(f"上次拜访：{body.last_visit}")
        if body.goal:
            parts.append(f"本次目标：{body.goal}")
        parts.append("请根据以上信息生成3条拜访理由建议。")
        return "\n".join(parts)

    def _call_ai_gateway(self, auth_header: str, body) -> dict:
        return call_ai_gateway(
            auth_header=auth_header,
            system_prompt=SYSTEM_PROMPT,
            user_message=self._build_user_message(body),
            temperature=0.7,
        )

    def _parse_reply(self, reply: str, body) -> dict:
        try:
            parsed = json.loads(reply)
            return {
                "hcp_name": body.hcp_name,
                "reasons": parsed if isinstance(parsed, list) else [],
            }
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("Failed to parse visit reason JSON: %s", exc)
            return self._build_fallback(body)

    def _build_fallback(self, body) -> dict:
        return {
            "hcp_name": getattr(body, "hcp_name", ""),
            "reasons": [
                {
                    "title": "常规学术拜访",
                    "detail": "了解医生近期临床需求和用药反馈",
                    "materials": ["产品资料", "最新临床研究"],
                    "priority": "中",
                }
            ],
        }
