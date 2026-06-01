from typing import Optional

from langchain_core.callbacks import BaseCallbackHandler


class TokenCallbackHandler(BaseCallbackHandler):
    def __init__(self, user_id: Optional[str] = None, budget_service=None):
        self.user_id = user_id
        self.budget_service = budget_service
        self.total_tokens = 0

    def on_llm_start(self, serialized, prompts, **kwargs):
        pass

    def on_llm_end(self, response, **kwargs):
        if hasattr(response, "llm_output") and response.llm_output:
            token_usage = response.llm_output.get("token_usage", {})
            tokens = token_usage.get("total_tokens", 0)
            self.total_tokens += tokens
            if self.budget_service and self.user_id:
                self.budget_service.record_usage(self.user_id, tokens)
