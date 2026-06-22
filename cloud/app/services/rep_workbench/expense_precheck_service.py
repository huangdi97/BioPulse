"""费用预检服务。交叉验证GPS/拜访/费用数据一致性。"""

import logging
from datetime import datetime, timezone

from shared.base_service import BaseService

logger = logging.getLogger(__name__)


class ExpensePrecheckService(BaseService):
    """交叉验证GPS轨迹、拜访记录与费用报销的一致性。"""

    def precheck(self, expense_id: int) -> dict:
        checks = {
            "gps_match": self._check_gps_match(expense_id),
            "visit_exists": self._check_visit_exists(expense_id),
            "amount_reasonable": self._check_amount_reasonable(expense_id),
            "time_consistency": self._check_time_consistency(expense_id),
        }
        passed = all(v["passed"] for v in checks.values())
        return {
            "expense_id": expense_id,
            "passed": passed,
            "checks": checks,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def _check_gps_match(self, expense_id: int) -> dict:
        conn = self._connection()
        cur = conn.execute(
            "SELECT location_lat, location_lng, location_name FROM expenses WHERE id = ?",
            (expense_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"passed": False, "reason": "费用记录不存在"}
        lat, lng, loc_name = row
        if not lat or not lng:
            return {"passed": False, "reason": "费用记录缺少GPS坐标"}
        visit_cur = conn.execute(
            "SELECT location_lat, location_lng FROM visits WHERE expense_id = ? AND is_active = 1",
            (expense_id,),
        )
        visit_row = visit_cur.fetchone()
        if not visit_row:
            return {"passed": True, "reason": "无关联拜访，跳过GPS校验"}
        v_lat, v_lng = visit_row
        if abs(lat - v_lat) > 0.01 or abs(lng - v_lng) > 0.01:
            return {
                "passed": False,
                "reason": f"费用坐标({lat},{lng})与拜访坐标({v_lat},{v_lng})偏差过大",
            }
        return {"passed": True, "reason": "GPS坐标匹配"}

    def _check_visit_exists(self, expense_id: int) -> dict:
        conn = self._connection()
        cur = conn.execute(
            "SELECT id, hcp_name, visit_date FROM visits WHERE expense_id = ? AND is_active = 1",
            (expense_id,),
        )
        row = cur.fetchone()
        if row:
            return {"passed": True, "visit_id": row[0], "hcp_name": row[1], "reason": "存在关联拜访"}
        return {"passed": False, "reason": "无关联拜访记录"}

    def _check_amount_reasonable(self, expense_id: int) -> dict:
        conn = self._connection()
        cur = conn.execute("SELECT amount, category FROM expenses WHERE id = ?", (expense_id,))
        row = cur.fetchone()
        if not row:
            return {"passed": False, "reason": "费用记录不存在"}
        amount, category = row
        limits = {"交通": 500, "餐饮": 300, "住宿": 800, "礼品": 200, "其他": 1000}
        limit = limits.get(category, 1000)
        if amount > limit:
            return {"passed": False, "reason": f"{category}费用{amount}元超出限额{limit}元"}
        return {"passed": True, "reason": f"{category}费用{amount}元在限额内"}

    def _check_time_consistency(self, expense_id: int) -> dict:
        conn = self._connection()
        cur = conn.execute(
            "SELECT e.expense_date, v.visit_date FROM expenses e LEFT JOIN visits v ON v.expense_id = e.id WHERE e.id = ?",
            (expense_id,),
        )
        row = cur.fetchone()
        if not row or not row[0]:
            return {"passed": False, "reason": "缺少费用日期"}
        expense_date = row[0]
        if row[1] and row[1] != expense_date:
            return {
                "passed": False,
                "reason": f"费用日期({expense_date})与拜访日期({row[1]})不一致",
            }
        return {"passed": True, "reason": "日期一致"}
