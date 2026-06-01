# FROZEN — 代码保留不迭代。参见一云四端-整体战略规划-v2.3-final.md 第2章
import hashlib
import json
import re
from datetime import datetime
from typing import Any, Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import DataMaskingRulesRepository, DpAuditLogRepository, PrivacyBudgetsRepository
from cloud.app.services.base import BaseService


def _rule_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "rule_name": row["rule_name"],
        "field_pattern": row["field_pattern"],
        "masking_type": row["masking_type"],
        "masking_config": row["masking_config"],
        "applies_to": row["applies_to"],
        "enabled": row["enabled"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _budget_to_dict(row) -> dict:
    ex = row["epsilon_spent"] / row["epsilon_total"] if row["epsilon_total"] > 0 else 0.0
    return {
        "id": row["id"],
        "did": row["did"],
        "epsilon_total": row["epsilon_total"],
        "epsilon_spent": row["epsilon_spent"],
        "epsilon_remaining": row["epsilon_remaining"],
        "query_count": row["query_count"],
        "last_query_at": row["last_query_at"],
        "reset_at": row["reset_at"],
        "created_at": row["created_at"],
        "exhaustion_ratio": round(ex, 4),
    }


def _apply_mask(value: str, masking_type: str, config: dict) -> str:
    if masking_type == "mask":
        rule = config.get("rule", "")
        if rule == "keep_first_last" and len(value) > 2:
            value = value[0] + "***" + value[-1]
        elif rule == "keep_first_3_last_4" and len(value) > 7:
            value = value[:3] + "****" + value[-4:]
        elif rule == "keep_last_4" and len(value) > 4:
            value = "***" + value[-4:]
        else:
            value = value[0] + "***" + value[-1] if len(value) > 2 else "***"
    elif masking_type == "truncate":
        max_len = config.get("max_length", 3)
        value = value[:max_len] + "..."
    elif masking_type == "hash":
        value = hashlib.sha256(value.encode()).hexdigest()[:16]
    elif masking_type == "generalize":
        label = config.get("label", "***")
        value = label
    elif masking_type == "suppress":
        value = ""
    return value


class PrivacyService(BaseService):
    def create_rule(
        self, rule_name: str, field_pattern: str, masking_type: str,
        masking_config: str, applies_to: str, user_id: int,
    ) -> dict:
        repo = DataMaskingRulesRepository(self.db)
        try:
            row_id = repo.create({
                "rule_name": rule_name,
                "field_pattern": field_pattern,
                "masking_type": masking_type,
                "masking_config": masking_config,
                "applies_to": applies_to,
                "created_by": user_id,
            })
            row = repo.get_by_id(row_id)
            return _rule_to_dict(row)
        except Exception as e:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))

    def list_rules(
        self, enabled: Optional[int] = None, masking_type: Optional[str] = None,
    ) -> list:
        repo = DataMaskingRulesRepository(self.db)
        conditions = []
        params: list[Any] = []
        if enabled is not None:
            conditions.append("enabled=?")
            params.append(enabled)
        if masking_type:
            conditions.append("masking_type=?")
            params.append(masking_type)
        rows = repo.list_all(
            conditions=conditions or None,
            params=params or None,
            order_by="id ASC",
        )
        return [_rule_to_dict(r) for r in rows]

    def toggle_rule(self, rule_id: int) -> dict:
        repo = DataMaskingRulesRepository(self.db)
        row = repo.get_by_id(rule_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Rule not found")
        now_iso = datetime.utcnow().isoformat()
        repo.update(rule_id, {
            "enabled": 0 if row["enabled"] else 1,
            "updated_at": now_iso,
        })
        row = repo.get_by_id(rule_id)
        return _rule_to_dict(row)

    def delete_rule(self, rule_id: int) -> None:
        repo = DataMaskingRulesRepository(self.db)
        row = repo.get_by_id(rule_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Rule not found")
        repo.delete(rule_id)

    def init_budget(self, did: str, epsilon_total: float) -> dict:
        repo = PrivacyBudgetsRepository(self.db)
        existing = repo.count(conditions=["did=?"], params=[did])
        if existing > 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Budget already exists for this DID")
        row_id = repo.create({
            "did": did,
            "epsilon_total": epsilon_total,
            "epsilon_spent": 0.0,
            "epsilon_remaining": epsilon_total,
        })
        row = repo.get_by_id(row_id)
        return _budget_to_dict(row)

    def get_budget_status(self, did: Optional[str] = None) -> dict | list:
        repo = PrivacyBudgetsRepository(self.db)
        if did:
            rows = repo.list_all(conditions=["did=?"], params=[did])
            if not rows:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Budget not found")
            return _budget_to_dict(rows[0])
        rows = repo.list_all(order_by="id ASC")
        return [_budget_to_dict(r) for r in rows]

    def reset_budget(self, did: str) -> dict:
        repo = PrivacyBudgetsRepository(self.db)
        rows = repo.list_all(conditions=["did=?"], params=[did])
        if not rows:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Budget not found")
        now_iso = datetime.utcnow().isoformat()
        repo.update(rows[0]["id"], {
            "epsilon_spent": 0.0,
            "epsilon_remaining": rows[0]["epsilon_total"],
            "query_count": 0,
            "reset_at": now_iso,
        })
        rows = repo.list_all(conditions=["did=?"], params=[did])
        return _budget_to_dict(rows[0])

    def mask_data(self, data: dict, rule_ids: Optional[list[int]] = None) -> dict:
        repo = DataMaskingRulesRepository(self.db)
        if rule_ids:
            ph = ",".join("?" * len(rule_ids))
            placeholders = ", ".join(repo.cols)
            rows = self.db.execute(
                f"SELECT {placeholders} FROM {repo.table_name} WHERE enabled=1 AND id IN ({ph}) ORDER BY id",
                rule_ids,
            ).fetchall()
            rows = [dict(r) for r in rows]
        else:
            rows = repo.list_all(conditions=["enabled=1"], order_by="id ASC")
        if not rows:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No enabled masking rules found")
        masked = {}
        for key, value in data.items():
            value_str = str(value) if value is not None else ""
            for rule_row in rows:
                pattern = rule_row["field_pattern"]
                try:
                    if re.search(pattern, key, re.IGNORECASE):
                        config = json.loads(rule_row["masking_config"]) if rule_row["masking_config"] else {}
                        value_str = _apply_mask(value_str, rule_row["masking_type"], config)
                        break
                except re.error:
                    if pattern.lower() in key.lower():
                        config = json.loads(rule_row["masking_config"]) if rule_row["masking_config"] else {}
                        value_str = _apply_mask(value_str, rule_row["masking_type"], config)
                        break
            masked[key] = value_str
        return {"masked": masked}

    def get_audit_log(
        self,
        did: Optional[str] = None,
        operation_type: Optional[str] = None,
        approved: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list:
        repo = DpAuditLogRepository(self.db)
        conditions = []
        params: list[Any] = []
        if did:
            conditions.append("did=?")
            params.append(did)
        if operation_type:
            conditions.append("operation_type=?")
            params.append(operation_type)
        if approved is not None:
            conditions.append("approved=?")
            params.append(approved)
        if start_date:
            conditions.append("created_at >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date)
        rows = repo.list_all(
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )
        return [dict(r) for r in rows]

    def get_dashboard(self) -> dict:
        rule_repo = DataMaskingRulesRepository(self.db)
        budget_repo = PrivacyBudgetsRepository(self.db)
        audit_repo = DpAuditLogRepository(self.db)

        total_rules = rule_repo.count()
        active_rules = rule_repo.count(conditions=["enabled=1"])
        total_budgets = budget_repo.count()
        total_queries = self.db.execute(
            f"SELECT COALESCE(SUM(query_count),0) FROM {budget_repo.table_name}"
        ).fetchone()[0]
        total_epsilon_spent = self.db.execute(
            f"SELECT COALESCE(SUM(epsilon_spent),0) FROM {budget_repo.table_name}"
        ).fetchone()[0]
        total_audits = audit_repo.count()
        audits_today = self.db.execute(
            f"SELECT COUNT(*) FROM {audit_repo.table_name} WHERE date(created_at)=date('now')"
        ).fetchone()[0]
        return {
            "total_rules": total_rules,
            "active_rules": active_rules,
            "total_budgets": total_budgets,
            "total_queries": total_queries,
            "total_epsilon_spent": round(total_epsilon_spent, 4),
            "total_audits": total_audits,
            "audits_today": audits_today,
        }
