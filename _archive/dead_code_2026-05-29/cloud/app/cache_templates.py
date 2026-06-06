class TemplateCache:
    TEMPLATES = {
        "你好": "你好！有什么可以帮助你的？",
        "hello": "Hello! How can I help you?",
        "在吗": "在的，有什么需要帮助的吗？",
        "谢谢": "不客气，随时为您服务。",
        "再见": "再见，祝您工作顺利！",
        "拜拜": "拜拜，再见！",
        "好的": "好的，已收到。",
        "知道了": "好的，已记录您的反馈。",
        "嗯": "好的，请继续。",
        "ok": "OK, noted.",
        "help": "I'm here to help. What would you like to know about?",
        "error_retry": "系统暂时遇到问题，请稍后重试。",
        "error_timeout": "请求超时，请检查网络后重试。",
        "not_found": "未找到相关信息，请尝试换个关键词搜索。",
    }

    def __init__(self):
        self._hit_count = 0

    def get(self, text: str):
        if not isinstance(text, str):
            return None
        normalized = text.strip().lower()
        if normalized in self.TEMPLATES:
            self._hit_count += 1
            return self.TEMPLATES[normalized]
        for key in self.TEMPLATES:
            if key in normalized or normalized in key:
                self._hit_count += 1
                return self.TEMPLATES[key]
        return None

    def match_count(self) -> int:
        return self._hit_count


def check_template(text: str):
    return TemplateCache().get(text)
