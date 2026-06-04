class AgentNotifier:
    def __init__(self, telegram_token: str | None = None, chat_id: str | None = None):
        self._telegram_token = telegram_token
        self._chat_id = chat_id

    def notify(self, agent_key: str, goal: str, status: str, elapsed_seconds: float, cost: dict) -> None:
        message = f"[Agent] {agent_key} | {status} | 耗时:{elapsed_seconds:.1f}s | Token:{cost.get('total_tokens', 0)}"
        print(message)
