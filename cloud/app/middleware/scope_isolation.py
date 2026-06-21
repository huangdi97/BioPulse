"""FastAPI 中间件：基于请求路径的 scope 隔离。

根据请求路径自动识别所需 scope（pharma / research），
并与当前上下文中的 scope 进行比对；若不匹配则返回 403。
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from cloud.app.core.scope_context import get_scope

SCOPE_ROUTES: dict[str, str] = {
    "/api/pharma/": "pharma",
    "/api/research/": "research",
}


async def scope_isolation_middleware(request: Request, call_next):
    """请求级别 scope 校验中间件。

    1. 按请求路径前缀判定所需 scope；
    2. 无匹配前缀的路径直接放行；
    3. 从 scope_context 读取当前 scope；
    4. scope 不匹配或未设置时返回 403 JSON。
    """
    required_scope: str | None = None
    for prefix, scope_name in SCOPE_ROUTES.items():
        if request.url.path.startswith(prefix):
            required_scope = scope_name
            break

    if required_scope is None:
        return await call_next(request)

    current_scope = get_scope()
    if current_scope is None or current_scope.get("scope") != required_scope:
        return JSONResponse(
            status_code=403,
            content={"detail": f"Forbidden: required scope '{required_scope}', but got '{current_scope.get('scope') if current_scope else None}'"},
        )

    return await call_next(request)
