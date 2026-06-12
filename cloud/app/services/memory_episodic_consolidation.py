"""情景记忆巩固：AI 驱动的记忆抽象与长期记忆巩固的提示词构建与回复解析。"""

import json


def build_consolidation_prompt(row):
    """构建记忆巩固的 AI 提示词，引导模型提炼情景记忆为结构化洞察。"""
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
    """解析 AI 巩固回复为结构化记忆条目，解析失败时回退默认值。"""
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
