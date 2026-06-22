"""拜访自动填表服务。接收拜访要点文本，调LLM提取结构化字段。"""

import json
import logging

from shared.ai_gateway import call_ai_gateway
from shared.base_service import BaseService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是一位医药代表拜访记录助手。请从用户输入的拜访要点文本中提取结构化信息。"
    "必须输出严格 JSON 格式，字段如下：\n"
    "{\n"
    '  "hcp_name": "医生姓名",\n'
    '  "hospital": "医院名称",\n'
    '  "department": "科室",\n'
    '  "visit_type": "拜访类型(日常拜访/学术拜访/科室会)",\n'
    '  "products_discussed": ["提及产品名称列表"],\n'
    '  "key_points": ["关键沟通要点列表"],\n'
    '  "next_steps": ["后续跟进事项列表"],\n'
    '  "sentiment": "医生态度(积极/中性/消极)",\n'
    '  "summary": "拜访摘要"\n'
    "}\n"
    "如某字段无对应信息，使用 null 或空数组。"
)


class VisitAutofillService(BaseService):
    """接收拜访要点文本，调用AI提取结构化字段用于自动填表。"""

    def extract(self, body, auth_header: str) -> dict:
        try:
            ai_data = self._call_ai_gateway(auth_header, body)
            reply = ai_data.get("reply", "")
        except Exception:
            logger.exception("VisitAutofill AI gateway call failed")
            return self._build_fallback(body.text)

        if not reply:
            return self._build_fallback(body.text)

        return self._parse_reply(reply, body.text)

    def _build_user_message(self, body) -> str:
        lines = [f"拜访要点文本：{body.text}"]
        if body.context:
            lines.append(f"补充背景：{body.context}")
        return "\n".join(lines)

    def _call_ai_gateway(self, auth_header: str, body) -> dict:
        return call_ai_gateway(
            auth_header=auth_header,
            system_prompt=SYSTEM_PROMPT,
            user_message=self._build_user_message(body),
            temperature=0.2,
        )

    def _parse_reply(self, reply: str, original_text: str) -> dict:
        try:
            parsed = json.loads(reply)
            return {
                "original_text": original_text,
                "extracted": parsed,
            }
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("Failed to parse autofill JSON: %s", exc)
            return self._build_fallback(original_text)

    def _build_fallback(self, text: str) -> dict:
        return {
            "original_text": text,
            "extracted": {
                "hcp_name": None,
                "hospital": None,
                "department": None,
                "visit_type": None,
                "products_discussed": [],
                "key_points": [text] if text else [],
                "next_steps": [],
                "sentiment": None,
                "summary": text,
            },
        }
