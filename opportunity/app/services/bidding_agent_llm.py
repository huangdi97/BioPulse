"""投标代理LLM服务，提供AI调用和招标扫描基础设施。"""

import json
import logging
import urllib.request
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from starlette import status

from opportunity.app.repositories import BiddingAgentLogRepository
from shared.app_settings import settings
from shared.base_service import BaseService

logger = logging.getLogger(__name__)

AI_GATEWAY_URL = f"{settings.cloud_api_base}/ai/chat"


class BiddingAgentLLM(BaseService):
    """招投标Agent LLM层：AI调用、招标扫描与分析、日志记录。"""

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
                    logger.exception("LLM调用异常")
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

    def get_all_active_configs(self, conn) -> list:
        """获取所有活跃的Agent配置（供调用方传入数据库连接）。"""
        configs = conn.execute("SELECT * FROM bidding_agent_config WHERE is_active = 1").fetchall()
        return [dict(c) for c in configs]

    def auto_analyze_bidding(self, bidding_id: int, auth_header: str) -> dict:
        """自动调用AI分析招标信息并更新分析结果。"""
        conn = self._connection()
        try:
            return self._update_bidding_analysis(conn, bidding_id, auth_header)
        finally:
            conn.close()

    def run_scheduled_scan(self) -> None:
        """定时扫描任务入口，遍历所有活跃配置执行招标信息抓取。"""
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
                    logger.exception("评分异常")
                    self._log_scan_result(conn, config["id"], "failed", 0, 0, str(e), started_at)
                conn.commit()
        finally:
            conn.close()
