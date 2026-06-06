"""医保目录查询服务。"""

from datetime import datetime, timezone

import httpx

from market_access.app.database import get_cache, set_cache
from shared.app_settings import settings

CLOUD_API = settings.cloud_api_base


async def get_formulary_status(drug_name: str) -> dict:
    """查询药品是否在医保目录内。

    调用 Cloud PubMed API 搜索药品相关论文/信息，
    模拟判定医保目录状态。
    """
    cache_key = f"formulary:status:{drug_name}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{CLOUD_API}/pubmed/search",
            json={
                "query": drug_name,
                "limit": 20,
            },
        )
        papers = []
        if resp.status_code == 200:
            data = resp.json()
            papers = data.get("data", data.get("papers", []))

    result = _assess_formulary_status(drug_name, papers)
    set_cache(cache_key, result, ttl=300)
    return result


def _assess_formulary_status(drug_name: str, papers: list) -> dict:
    """基于论文信息模拟评估医保目录状态。"""
    pub_count = len(papers)
    in_formulary = pub_count > 0

    if in_formulary:
        rate = "70%" if pub_count > 5 else "50%"
        restrictions = "限二级以上医院使用" if pub_count > 10 else "限特定适应症"
    else:
        rate = "未纳入"
        restrictions = "尚未进入医保目录"

    return {
        "drug_name": drug_name,
        "in_formulary": in_formulary,
        "reimbursement_rate": rate,
        "restrictions": restrictions,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


async def get_reimbursement_info(drug_name: str) -> dict:
    """获取药品报销信息。

    调用 Cloud PubMed API 搜索药品信息，
    模拟返回报销比例、限制条件等。
    """
    cache_key = f"formulary:reimbursement:{drug_name}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{CLOUD_API}/pubmed/search",
            json={
                "query": f"{drug_name} reimbursement",
                "limit": 20,
            },
        )
        papers = []
        if resp.status_code == 200:
            data = resp.json()
            papers = data.get("data", data.get("papers", []))

    result = _assess_reimbursement(drug_name, papers)
    set_cache(cache_key, result, ttl=300)
    return result


def _assess_reimbursement(drug_name: str, papers: list) -> dict:
    """模拟评估报销信息。"""
    pub_count = len(papers)
    in_formulary = pub_count > 0

    if in_formulary:
        rate = "80%" if pub_count > 10 else "60%"
        restrictions = "乙类药品，先自付10%" if pub_count > 5 else "丙类，完全自费"
    else:
        rate = "未纳入"
        restrictions = "尚未进入医保目录，需自费"

    return {
        "drug_name": drug_name,
        "in_formulary": in_formulary,
        "reimbursement_rate": rate,
        "restrictions": restrictions,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
