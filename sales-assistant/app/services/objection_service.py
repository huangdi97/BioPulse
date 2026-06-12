"""异议处理服务：AI驱动的客户异议分析与应答建议。"""

import json
import logging
import urllib.error
from typing import Any

from shared.ai_gateway import call_ai_gateway
from shared.base_service import BaseService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是一位资深的医药销售培训师，拥有丰富的临床推广经验和销售培训经历。"
    "你的任务是根据客户提出的异议，给出专业、实用的应答建议。"
    "请保持中立、合规的立场，不承诺无法实现的事情，不贬低竞品。"
    "回复必须严格使用以下JSON格式："
    '{"analysis":"...","response_suggestion":"...","key_points":["..."],"do_not_say":["..."]}'
)


class ObjectionService(BaseService):
    """异议处理服务：调用AI网关解析客户异议并生成专业应答。"""

    def _build_user_message(self, body) -> str:
        parts = [f"客户异议：{body.objection}"]
        if body.customer_type:
            parts.append(f"客户类型：{body.customer_type}")
        if body.context:
            parts.append(f"场景：{body.context}")
        parts.append("请给出专业的应答建议。")
        return "\n".join(parts)

    def _build_fallback_response(self, body) -> dict:
        return {
            "objection": body.objection,
            "analysis": "暂时无法生成详细的分析，请从产品特性、安全数据、经济性等角度综合考量。",
            "response_suggestion": (
                "感谢您提出的宝贵意见。我们会详细记录并反馈给相关部门。同时，我可以提供更多关于产品临床数据的信息，帮助您更全面地了解我们的产品。"
            ),
            "key_points": [
                "强调产品的核心临床获益",
                "提供循证医学数据支持",
                "了解客户更深层的顾虑",
            ],
            "do_not_say": [
                "不要直接贬低竞争对手",
                "不要承诺无法实现的折扣或利益",
                "不要回避客户的核心关切",
            ],
        }

    def _call_ai_gateway(self, auth_header: str, body) -> dict[str, Any]:
        return call_ai_gateway(
            auth_header=auth_header,
            system_prompt=SYSTEM_PROMPT,
            user_message=self._build_user_message(body),
        )

    def _parse_objection(self, raw_reply: str, body) -> dict:
        try:
            parsed = json.loads(raw_reply)
            return {
                "objection": body.objection,
                "analysis": parsed.get("analysis", ""),
                "response_suggestion": parsed.get("response_suggestion", ""),
                "key_points": parsed.get("key_points", []),
                "do_not_say": parsed.get("do_not_say", []),
            }
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("Failed to parse AI objection JSON: %s, using fallback", exc)
            return self._build_fallback_response(body)

    def handle_objection(self, body, auth_header: str = "") -> dict:
        """处理客户异议，调用AI生成专业应答建议。

        Args:
            body: 异议请求体，含客户异议、客户类型、场景等。
            auth_header: 认证头信息。

        Returns:
            包含分析、应答建议、关键点和禁忌事项的字典。
        """
        try:
            ai_data = self._call_ai_gateway(auth_header, body)
            reply = ai_data.get("reply", "")
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            logger.warning("AI gateway unavailable: %s, using fallback", exc)
            reply = ""
        except Exception:
            logger.exception("Unexpected error calling AI gateway")
            reply = ""

        if reply:
            return self._parse_objection(reply, body)
        return self._build_fallback_response(body)
