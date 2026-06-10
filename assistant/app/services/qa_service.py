"""问答服务模块。"""

import json
import logging
import urllib.error

from shared.ai_gateway import call_ai_gateway
from shared.base_service import BaseService

TIMEOUT_SECONDS = 30
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是一位资深临床药师，拥有丰富的医药学知识和临床实践经验。"
    "请以专业、客观、循证的角度回答用户提出的医学问题。"
    "回答时应引用权威指南、临床研究或药品说明书，若缺乏依据请明确说明。"
    "回答结束后用 JSON 格式输出，格式为："
    '{"answer":"你的回答内容","sources":["信息来源1","信息来源2"]}'
)


class QaService(BaseService):
    """问答服务，调用AI网关进行临床药学问答。"""

    def answer_question(self, body, auth_header: str) -> dict:
        """调用AI网关进行临床药学问答。

        Args:
            body: 包含 question 和 context 的请求体; auth_header: 认证头

        Returns:
            dict: 包含 question、answer、sources 的问答结果
        """
        try:
            ai_data = self._call_ai_gateway(auth_header, body)
            reply = ai_data.get("reply", "")
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            logger.warning("AI gateway unavailable: %s, using fallback", exc)
            return self._build_fallback_qa(body.question)
        except Exception:
            logger.exception("Unexpected error calling AI gateway")
            return self._build_fallback_qa(body.question)

        if not reply:
            return self._build_fallback_qa(body.question)

        return self._parse_qa_response(reply, body.question)

    def _build_user_message(self, body) -> str:
        lines = [f"问题：{body.question}"]
        if body.context:
            lines.append(f"背景信息：{body.context}")
        lines.append("请以资深临床药师的身份回答。")
        return "\n".join(lines)

    def _call_ai_gateway(self, auth_header: str, body) -> dict:
        return call_ai_gateway(
            auth_header=auth_header,
            system_prompt=SYSTEM_PROMPT,
            user_message=self._build_user_message(body),
            temperature=0.3,
        )

    def _parse_qa_response(self, reply: str, question: str) -> dict:
        try:
            parsed = json.loads(reply)
            return {
                "question": question,
                "answer": parsed.get("answer", ""),
                "sources": parsed.get("sources", []),
            }
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("Failed to parse AI QA JSON: %s, using raw reply", exc)
            return {
                "question": question,
                "answer": reply,
                "sources": [],
            }

    def _build_fallback_qa(self, question: str) -> dict:
        return {
            "question": question,
            "answer": "很抱歉，AI医学问答服务暂时不可用，请稍后重试。",
            "sources": [],
        }
