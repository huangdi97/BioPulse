"""记忆格式化和AI调用辅助函数。"""

import json
import urllib.request
from datetime import datetime

from shared.config import settings as config_settings


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _call_ai(messages: list[dict], auth_header: str) -> dict:
    payload = {"messages": messages, "temperature": 0.3, "max_tokens": 2048}
    req = urllib.request.Request(
        f"{config_settings.ai_chat_url}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": auth_header},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as rp:
        return json.loads(rp.read().decode("utf-8")).get("data", {})


def build_consolidation_prompt(row):
    return [
        {
            "role": "system",
            "content": "你是一名记忆巩固专家。请根据输入的情景记忆内容，提炼核心洞察，生成结构化的记忆条目。"
            '输出纯JSON（不要markdown代码块）：{"title":"洞察标题","content":"详细内容","memory_type":"insight",'
            '"importance":0.8,"context_tags":["标签1","标签2"]}',
        },
        {
            "role": "user",
            "content": f"事件类型: {row['event_type']}\n标题: {row['title']}\n"
            f"描述: {row['description']}\n情景: {row['context']}\n结果: {row['outcome']}\n"
            f"情感值: {row['valence']}\n强度: {row['intensity']}",
        },
    ]


def parse_consolidation_reply(reply, row):
    try:
        return json.loads(reply)
    except (json.JSONDecodeError, TypeError):
        return {
            "title": row["title"],
            "content": reply or row["description"],
            "memory_type": "insight",
            "importance": 0.5,
            "context_tags": [],
        }


def build_abstract_prompt(rows, abstraction_level, txt):
    return [
        {
            "role": "system",
            "content": f'语义抽象层次={abstraction_level}。输出JSON:{{"title":"","content":"","context_tags":[]}}',
        },
        {"role": "user", "content": txt},
    ]


def parse_abstract_reply(reply, source_type, fallback_txt=""):
    try:
        return json.loads(reply)
    except Exception:
        return {
            "title": f"Semantic-{source_type}",
            "content": reply or fallback_txt,
            "context_tags": [],
        }
