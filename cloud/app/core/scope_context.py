from contextvars import ContextVar, Token
from typing import Any

_scope_var: ContextVar[dict[str, Any] | None] = ContextVar("scope", default=None)


def set_scope(scope: dict[str, Any] | None) -> Token[dict[str, Any] | None]:
    return _scope_var.set(scope)


def get_scope() -> dict[str, Any] | None:
    return _scope_var.get()


def reset_scope(token: Token[dict[str, Any] | None]) -> None:
    _scope_var.reset(token)
