"""Management service shared utilities."""

import logging

import httpx

from shared.ai_gateway import INTERNAL_API_TIMEOUT
from shared.app_settings import settings

logger = logging.getLogger(__name__)
CLOUD_API = settings.cloud_api_base


async def fetch(path: str) -> dict:
    """Fetch data from cloud API with error handling."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{CLOUD_API}{path}", timeout=INTERNAL_API_TIMEOUT)
            return resp.json() if resp.status_code == 200 else {}
        except Exception:
            logger.warning("Management service数据获取异常", exc_info=True)
            return {}
