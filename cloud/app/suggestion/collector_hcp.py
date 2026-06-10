"""HCP 画像收集来源。"""

from __future__ import annotations

import sqlite3
from typing import Any


def query_hcp_profile(db: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    """查询 HCP 统一画像。

    Args:
        db: 数据库连接（未使用，保持接口一致）。
        args: 包含 hcp_id 的参数。

    Returns:
        HCP 画像字典。
    """
    from ..services.hcp_mdm_service import get_unified_profile

    profile = get_unified_profile(str(args.get("hcp_id", "")))
    if hasattr(profile, "model_dump"):
        return profile.model_dump()
    return dict(profile)
