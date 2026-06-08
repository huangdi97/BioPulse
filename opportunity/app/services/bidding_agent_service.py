"""投标代理服务，用于自动处理投标流程和智能投标建议。"""

from datetime import datetime, timezone

from fastapi import HTTPException
from starlette import status

from opportunity.app.repositories import BiddingAgentConfigRepository
from opportunity.app.services.base import BaseCrudService
from opportunity.app.services.bidding_agent_llm import BiddingAgentLLM


class BiddingAgentService(BiddingAgentLLM, BaseCrudService):
    """招投标Agent调度：管理Agent配置、触发扫描、分析招标信息、记录运行日志。"""

    def __init__(self, db=None):
        BaseCrudService.__init__(self, repository_class=BiddingAgentConfigRepository, entity_name="Config", db=db)

    def create_agent_config(self, body, user_id: int) -> int:
        """创建投标Agent配置。

        Args:
            body: 投标Agent配置请求体。
            user_id: 创建人用户ID。

        Returns:
            新配置ID。

        Raises:
            sqlite3.Error: 当配置写入失败时由仓储层抛出。
        """
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
            self._close_connection(conn)

    def list_agent_configs(self) -> list:
        """列出所有活跃投标Agent配置。

        Args:
            None.

        Returns:
            活跃配置字典列表。

        Raises:
            sqlite3.Error: 当配置查询失败时由仓储层抛出。
        """
        conn = self._connection()
        try:
            repo = BiddingAgentConfigRepository(conn)
            rows = repo.list_all(conditions=["is_active = 1"], order_by="id DESC")
            return [dict(r) for r in rows]
        finally:
            self._close_connection(conn)

    def update_agent_config(self, config_id: int, body) -> dict:
        """更新投标Agent配置。

        Args:
            config_id: 配置ID。
            body: 配置更新请求体。

        Returns:
            更新后的配置字典；无更新字段时返回原配置。

        Raises:
            HTTPException: 当配置不存在或已停用时抛出404。
            sqlite3.Error: 当配置更新失败时由仓储层抛出。
        """
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
            self._close_connection(conn)

    def delete_agent_config(self, config_id: int) -> None:
        """软删除投标Agent配置。

        Args:
            config_id: 配置ID。

        Returns:
            None。

        Raises:
            HTTPException: 当配置不存在或已停用时抛出404。
            sqlite3.Error: 当软删除失败时由仓储层抛出。
        """
        conn = self._connection()
        try:
            repo = BiddingAgentConfigRepository(conn)
            row = repo.get_by_id(config_id)
            if not row or row["is_active"] != 1:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Config not found")
            repo.soft_delete(config_id)
        finally:
            self._close_connection(conn)

    def trigger_scan(self, auth_header: str) -> dict:
        """按所有活跃配置触发一次投标扫描。

        Args:
            auth_header: 透传给LLM或外部扫描流程的认证头。

        Returns:
            包含发现数量、解析数量和错误列表的扫描摘要。

        Raises:
            sqlite3.Error: 当配置读取或日志写入失败时抛出。
        """
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
            self._close_connection(conn)

    def get_agent_status(self) -> dict:
        """读取投标Agent最近运行状态。

        Args:
            None.

        Returns:
            最近运行时间、总运行次数和成功率。

        Raises:
            sqlite3.Error: 当状态统计查询失败时抛出。
        """
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
            self._close_connection(conn)

    def list_agent_logs(self, page: int, page_size: int) -> tuple:
        """分页列出投标Agent运行日志。

        Args:
            page: 当前页码。
            page_size: 每页数量。

        Returns:
            包含日志列表、总数、页码、页大小和总页数的元组。

        Raises:
            sqlite3.Error: 当日志查询失败时抛出。
        """
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
            self._close_connection(conn)
