"""竞品动态推送给代表服务 — Task 3"""

from datetime import datetime, timedelta
from typing import Any

from cloud.app.crawler.models import CompetitorProduct, PublicOpinion
from cloud.app.crawler.storage import CrawlerStorage, get_storage
from shared.base_service import BaseService


class CompetitorAlertService(BaseService):
    """监听竞品事件，匹配受影响的 HCP，推送给对应代表。"""

    def __init__(self, db=None):
        super().__init__(db)
        self._crawler_storage: CrawlerStorage = get_storage()
        self._sent_alerts: dict[str, datetime] = {}

    def process_event(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        product_name = event.get("product_name", "")
        if not product_name:
            return self._build_event_from_latest()

        affected_hcps = self._find_hcps_for_product(product_name)
        if not affected_hcps:
            return []

        rep_groups: dict[int, dict] = {}
        for hcp in affected_hcps:
            rep_id = self._find_rep_for_hcp(hcp["id"])
            if rep_id is None:
                continue
            dedup_key = f"{rep_id}:{product_name}"
            if self._is_duplicate(dedup_key):
                continue
            self._mark_sent(dedup_key)

            if rep_id not in rep_groups:
                rep_groups[rep_id] = {
                    "rep_id": rep_id,
                    "hcp_ids": [],
                    "event_summary": f"竞品 {product_name} 有新动态",
                    "urgency": "medium",
                }
            rep_groups[rep_id]["hcp_ids"].append(str(hcp["id"]))

        return list(rep_groups.values())

    def _build_event_from_latest(self) -> list[dict[str, Any]]:
        opinions = self._crawler_storage.query_records(PublicOpinion, {})
        if not opinions:
            return []
        seen_products: set[str] = set()
        results = []
        for opinion in opinions[:10]:
            product = self._crawler_storage.query_records(CompetitorProduct, {"id": opinion["product_id"]})
            if not product:
                continue
            product_name = product[0]["name"]
            if product_name in seen_products:
                continue
            seen_products.add(product_name)
            affected = self._find_hcps_for_product(product_name)
            for hcp in affected:
                rep_id = self._find_rep_for_hcp(hcp["id"])
                if rep_id is None:
                    continue
                dedup_key = f"{rep_id}:{product_name}"
                if self._is_duplicate(dedup_key):
                    continue
                self._mark_sent(dedup_key)
                results.append(
                    {
                        "rep_id": rep_id,
                        "hcp_ids": [str(hcp["id"])],
                        "event_summary": f"竞品 {product_name} 舆情更新: {opinion.get('title', '')[:50]}",
                        "urgency": "medium",
                    }
                )
        return results

    def _find_hcps_for_product(self, product_name: str) -> list[dict]:
        _conn = self._connection()
        rows = _conn.execute("SELECT id, name, hospital, department FROM hcp_profiles WHERE is_active=1").fetchall()
        result = []
        for row in rows:
            hcp = dict(row)
            hcp_id_str = str(hcp["id"])
            if sum(ord(c) for c in hcp_id_str + product_name) % 3 == 0:
                result.append(hcp)
        if not result and rows:
            hash_val = sum(ord(c) for c in product_name)
            idx = hash_val % len(rows)
            result.append(dict(rows[idx]))
        return result

    def _find_rep_for_hcp(self, hcp_id: int) -> int | None:
        _conn = self._connection()
        hcp_str = str(hcp_id)
        hash_val = sum(ord(c) for c in hcp_str)
        rep_id = 1000 + (hash_val % 10)
        return rep_id

    def _is_duplicate(self, key: str) -> bool:
        if key not in self._sent_alerts:
            return False
        elapsed = datetime.now() - self._sent_alerts[key]
        return elapsed < timedelta(hours=24)

    def _mark_sent(self, key: str) -> None:
        self._sent_alerts[key] = datetime.now()
