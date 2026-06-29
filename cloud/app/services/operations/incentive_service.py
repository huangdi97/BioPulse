"""激励规则服务，管理激励规则的配置、试算、审批与查询。"""

from typing import Optional


class IncentiveService:
    _store: dict[int, dict] = {}
    _next_id: int = 1

    def configure_rules(
        self,
        name: str,
        rule_type: str,
        conditions: dict,
        reward: dict,
        description: Optional[str] = None,
    ) -> dict:
        """配置一条激励规则。

        Args:
            name: 规则名称。
            rule_type: 规则类型（如 rebate / bonus / commission）。
            conditions: 触发条件，例如 {"min_sales": 100000, "region": "east"}。
            reward: 奖励定义，例如 {"percentage": 5, "cap": 50000}。
            description: 规则说明。

        Returns:
            新建的激励规则字典。
        """
        rid = self._next_id
        self._next_id += 1
        record = {
            "id": rid,
            "name": name,
            "rule_type": rule_type,
            "conditions": conditions,
            "reward": reward,
            "description": description or "",
            "status": "draft",
            "approved_by": None,
        }
        self._store[rid] = record
        return record

    def calculate_bonus(self, rule_id: int, actuals: dict) -> dict:
        """根据实际业绩计算应发奖金。

        Args:
            rule_id: 激励规则 ID。
            actuals: 实际业绩数据，例如 {"sales": 120000, "new_clients": 8}。

        Returns:
            计算结果字典，包含是否达标、奖金金额、明细等。

        Raises:
            ValueError: 规则不存在。
        """
        rule = self._store.get(rule_id)
        if not rule:
            raise ValueError(f"Incentive rule {rule_id} not found")

        conditions = rule["conditions"]
        reward = rule["reward"]
        met = all(actuals.get(k) >= v if isinstance(v, (int, float)) else actuals.get(k) == v for k, v in conditions.items())
        bonus = 0
        if met:
            base = actuals.get("sales", 0)
            pct = reward.get("percentage", 0)
            cap = reward.get("cap")
            bonus = round(base * pct / 100, 2)
            if cap is not None:
                bonus = min(bonus, cap)

        return {
            "rule_id": rule_id,
            "rule_name": rule["name"],
            "conditions_met": met,
            "bonus": bonus,
            "details": {"applied_percentage": reward.get("percentage", 0)},
        }

    def simulate(self, rule_id: int, hypotheticals: list[dict]) -> list[dict]:
        """模拟多条假设业绩下的奖金结果。

        Args:
            rule_id: 激励规则 ID。
            hypotheticals: 假设场景列表，每项为一个业绩 dict。

        Returns:
            每个假设场景对应的试算结果列表。

        Raises:
            ValueError: 规则不存在。
        """
        rule = self._store.get(rule_id)
        if not rule:
            raise ValueError(f"Incentive rule {rule_id} not found")

        results = []
        for i, h in enumerate(hypotheticals):
            conditions = rule["conditions"]
            reward = rule["reward"]
            met = all(h.get(k) >= v if isinstance(v, (int, float)) else h.get(k) == v for k, v in conditions.items())
            bonus = 0
            if met:
                base = h.get("sales", 0)
                pct = reward.get("percentage", 0)
                cap = reward.get("cap")
                bonus = round(base * pct / 100, 2)
                if cap is not None:
                    bonus = min(bonus, cap)
            results.append(
                {
                    "scenario_index": i,
                    "inputs": h,
                    "conditions_met": met,
                    "bonus": bonus,
                }
            )
        return results

    def approve(self, rule_id: int, approver: str) -> dict:
        """审批通过一条激励规则。

        Args:
            rule_id: 激励规则 ID。
            approver: 审批人标识。

        Returns:
            更新后的规则字典。

        Raises:
            ValueError: 规则不存在或状态不允许审批。
        """
        rule = self._store.get(rule_id)
        if not rule:
            raise ValueError(f"Incentive rule {rule_id} not found")
        if rule["status"] != "draft":
            raise ValueError(f"Rule {rule_id} is not in draft status")
        rule["status"] = "approved"
        rule["approved_by"] = approver
        return rule

    def get_detail(self, rule_id: int) -> dict:
        """查询单条激励规则的完整信息。

        Args:
            rule_id: 激励规则 ID。

        Returns:
            规则详情字典。

        Raises:
            ValueError: 规则不存在。
        """
        rule = self._store.get(rule_id)
        if not rule:
            raise ValueError(f"Incentive rule {rule_id} not found")
        return dict(rule)
