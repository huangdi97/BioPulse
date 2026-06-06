"""投标代理服务，用于自动处理投标流程和智能投标建议。"""

from datetime import datetime, timezone

from fastapi import HTTPException
from starlette import status

from opportunity.app.repositories import BiddingAgentConfigRepository
from opportunity.app.services.bidding_agent_llm import BiddingAgentLLM


class BiddingAgentService(BiddingAgentLLM):
    """招投标Agent调度：管理Agent配置、触发扫描、分析招标信息、记录运行日志。"""

    def create_agent_config(self, body, user_id: int) -> int:
        conn = self._connection()
        try:
            repo = BiddingAgentConfigRepository(conn)
            now = datetime.now(timezone.utc).isoformat()
            return repo.create(
                body.model_dump(),
                extra={
                    "created_by": user_id,
                    "created_at": now,
                    "updated_at": now,
                },
            )
        finally:
            conn.close()

    def list_agent_configs(self) -> list:
        conn = self._connection()
        try:
            repo = BiddingAgentConfigRepository(conn)
            rows = repo.list_all(conditions=["is_active = 1"], order_by="id DESC")
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def update_agent_config(self, config_id: int, body) -> dict:
        conn = self._connection()
        try:
            repo = BiddingAgentConfigRepository(conn)
            row = repo.get_by_id(config_id)
            if not row or row["is_active"] != 1:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Config not found")
            updates = body.model_dump(exclude_unset=True)
            if not updates:
                return dict(row)
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            repo.update(config_id, updates)
            return dict(repo.get_by_id(config_id))
        finally:
            conn.close()

    def delete_agent_config(self, config_id: int) -> None:
        conn = self._connection()
        try:
            repo = BiddingAgentConfigRepository(conn)
            row = repo.get_by_id(config_id)
            if not row or row["is_active"] != 1:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Config not found")
            repo.soft_delete(config_id)
        finally:
            conn.close()

    def trigger_scan(self, auth_header: str) -> dict:
        conn = self._connection()
        try:
            repo = BiddingAgentConfigRepository(conn)
            configs = repo.list_all(conditions=["is_active = 1"])
            if not configs:
                return {"total_found": 0, "total_parsed": 0, "errors": []}
            total_found = 0
            total_parsed = 0
            errors = []
            for cfg in configs:
                config = dict(cfg)
                started_at = datetime.now(timezone.utc).isoformat()
                try:
                    scan_result = self._run_scan_for_config(conn, auth_header, config)
                    total_found += scan_result["items_found"]
                    total_parsed += scan_result["items_parsed"]
                    self._log_scan_result(
                        conn,
                        config["id"],
                        "success",
                        scan_result["items_found"],
                        scan_result["items_parsed"],
                        None,
                        started_at,
                    )
                except Exception as e:
                    errors.append({"config_id": config["id"], "error": str(e)})
                    self._log_scan_result(conn, config["id"], "failed", 0, 0, str(e), started_at)
            return {
                "total_found": total_found,
                "total_parsed": total_parsed,
                "errors": errors,
            }
        finally:
            conn.close()

    def get_agent_status(self) -> dict:
        conn = self._connection()
        try:
            last = conn.execute("SELECT started_at FROM bidding_agent_log ORDER BY id DESC LIMIT 1").fetchone()
            stats = conn.execute(
                "SELECT COUNT(*) as total, SUM(CASE WHEN run_status='success' THEN 1 ELSE 0 END) as success FROM bidding_agent_log"
            ).fetchone()
            total_runs = stats["total"] or 0
            success_count = stats["success"] or 0
            success_rate = round(success_count / total_runs * 100, 1) if total_runs > 0 else 0.0
            return {
                "last_run": last["started_at"] if last else None,
                "total_runs": total_runs,
                "success_rate": success_rate,
            }
        finally:
            conn.close()

    def list_agent_logs(self, page: int, page_size: int) -> tuple:
        conn = self._connection()
        try:
            count_row = conn.execute("SELECT COUNT(*) FROM bidding_agent_log").fetchone()
            total = count_row[0]
            total_pages = max(1, (total + page_size - 1) // page_size)
            offset = (page - 1) * page_size
            rows = conn.execute(
                "SELECT * FROM bidding_agent_log ORDER BY id DESC LIMIT ? OFFSET ?",
                [page_size, offset],
            ).fetchall()
            items = [dict(r) for r in rows]
            return items, total, page, page_size, total_pages
        finally:
            conn.close()
