import json
import urllib.request
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from starlette import status

from opportunity.app.repositories import (
    BiddingAgentConfigRepository,
    BiddingAgentLogRepository,
)
from opportunity.app.services.base import BaseService

AI_GATEWAY_URL = "http://localhost:8000/ai/chat"


class BiddingAgentService(BaseService):
    """招投标Agent调度：管理Agent配置、触发扫描、分析招标信息、记录运行日志。"""

    def _call_llm(self, auth_header: str, prompt: str) -> str:
        req_body = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 2048,
        }
        req = urllib.request.Request(
            AI_GATEWAY_URL,
            data=json.dumps(req_body).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": auth_header},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
        envelope = json.loads(raw)
        data = envelope.get("data", {})
        return data.get("reply", "") if isinstance(data, dict) else str(data)

    def _parse_bids(self, reply: str) -> list:
        try:
            bids = json.loads(reply)
            return [bids] if isinstance(bids, dict) else bids
        except (json.JSONDecodeError, TypeError):
            return []

    def _run_scan_for_config(self, conn, auth_header: str, config: dict) -> dict:
        keywords = config.get("keywords", "")
        prompt = f"生成3条模拟的医药招标信息，关键词涉及: {keywords}。包含标题、医院、科室、预算、截止日期、产品类别。返回JSON数组"
        reply = self._call_llm(auth_header, prompt)
        bids = self._parse_bids(reply)
        found = 0
        parsed = 0
        for bid in bids:
            if not isinstance(bid, dict):
                continue
            found += 1
            title = bid.get("title", "") or bid.get("招标标题", "")
            if not title:
                continue
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "INSERT INTO bidding_info (title, hospital, department, product_category, budget, deadline, status, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)",
                (
                    title,
                    bid.get("hospital", "") or bid.get("医院", ""),
                    bid.get("department", "") or bid.get("科室", ""),
                    bid.get("product_category", "") or bid.get("产品类别", ""),
                    bid.get("budget", 0) or bid.get("预算", 0),
                    bid.get("deadline", "") or bid.get("截止日期", ""),
                    1,
                    now,
                    now,
                ),
            )
            parsed += 1
            if config.get("auto_notify") and config.get("notify_to"):
                try:
                    from shared.notification_client import send_notification

                    send_notification(
                        conn,
                        config["notify_to"],
                        f"新招标: {title}",
                        f"关键词: {keywords}",
                        "bidding_agent",
                        "bidding_info",
                        None,
                        {"config_id": config["id"]},
                    )
                except Exception:
                    pass
        return {"items_found": found, "items_parsed": parsed}

    def _log_scan_result(
        self,
        conn,
        config_id: int,
        status_: str,
        found: int,
        parsed: int,
        err: Optional[str],
        started: str,
    ):
        log_repo = BiddingAgentLogRepository(conn)
        completed = datetime.now(timezone.utc).isoformat()
        log_repo.create(
            {
                "config_id": config_id,
                "run_status": status_,
                "items_found": found,
                "items_parsed": parsed,
                "error_message": err,
                "started_at": started,
                "completed_at": completed,
                "created_at": completed,
            }
        )

    def _update_bidding_analysis(self, conn, bidding_id: int, auth_header: str) -> dict:
        row = conn.execute("SELECT * FROM bidding_info WHERE id = ? AND is_active = 1", (bidding_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bidding not found")
        bid = dict(row)
        prompt = f"""分析以下招标信息的机会评估和产品匹配建议:
标题: {bid.get("title", "")}
医院: {bid.get("hospital", "")}
科室: {bid.get("department", "")}
产品类别: {bid.get("product_category", "")}
预算: {bid.get("budget", "")}
截止日期: {bid.get("deadline", "")}
请返回JSON格式: {{"opportunity_assessment": "...", "product_suggestions": ["..."], "risk_factors": ["..."], "next_steps": ["..."]}}"""
        reply = self._call_llm(auth_header, prompt)
        try:
            analysis = json.loads(reply)
        except (json.JSONDecodeError, TypeError):
            analysis = {
                "opportunity_assessment": reply[:200],
                "product_suggestions": [],
                "risk_factors": [],
                "next_steps": [],
            }
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "UPDATE bidding_info SET analysis = ?, updated_at = ? WHERE id = ?",
            (json.dumps(analysis, ensure_ascii=False), now, bidding_id),
        )
        conn.commit()
        return analysis

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

    def auto_analyze_bidding(self, bidding_id: int, auth_header: str) -> dict:
        conn = self._connection()
        try:
            return self._update_bidding_analysis(conn, bidding_id, auth_header)
        finally:
            conn.close()

    def get_all_active_configs(self, conn) -> list:
        configs = conn.execute("SELECT * FROM bidding_agent_config WHERE is_active = 1").fetchall()
        return [dict(c) for c in configs]

    def run_scheduled_scan(self) -> None:
        conn = self._connection()
        try:
            configs = self.get_all_active_configs(conn)
            if not configs:
                return
            for cfg in configs:
                config = dict(cfg)
                started_at = datetime.now(timezone.utc).isoformat()
                try:
                    result = self._run_scan_for_config(conn, "", config)
                    self._log_scan_result(
                        conn,
                        config["id"],
                        "success",
                        result["items_found"],
                        result["items_parsed"],
                        None,
                        started_at,
                    )
                except Exception as e:
                    self._log_scan_result(conn, config["id"], "failed", 0, 0, str(e), started_at)
                conn.commit()
        finally:
            conn.close()
