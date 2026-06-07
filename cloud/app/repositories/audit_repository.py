"""审计日志、审计链、联邦审计、基准报告等数据访问层。"""

from cloud.shared.repository import BaseRepository
from shared.columns import (
    TABLE_AUDIT_CHAIN_BLOCKS_COLS,
    TABLE_AUDIT_CHAIN_ENTRIES_COLS,
    TABLE_AUDIT_LOGS_COLS,
    TABLE_BENCHMARK_REPORTS_COLS,
    TABLE_DP_AUDIT_LOG_COLS,
    TABLE_FED_AUDIT_CONTRIBUTIONS_COLS,
    TABLE_FEDERATED_NODES_COLS,
    TABLE_FEDERATED_ROUNDS_COLS,
)


class AuditLogsRepository(BaseRepository):
    """审计日志表。"""

    def __init__(self, db):
        super().__init__(db, "audit_logs", TABLE_AUDIT_LOGS_COLS)


class AuditChainEntriesRepository(BaseRepository):
    """审计链条目表。"""

    def __init__(self, db):
        super().__init__(db, "audit_chain_entries", TABLE_AUDIT_CHAIN_ENTRIES_COLS)


class DpAuditLogRepository(BaseRepository):
    """差分隐私审计日志表。"""

    def __init__(self, db):
        super().__init__(db, "dp_audit_log", TABLE_DP_AUDIT_LOG_COLS)


class FedAuditContributionsRepository(BaseRepository):
    """联邦审计贡献表。"""

    def __init__(self, db):
        super().__init__(db, "fed_audit_contributions", TABLE_FED_AUDIT_CONTRIBUTIONS_COLS)

    def list_filtered(self, contributor_did=None, contribution_type=None, verified=None):
        conditions, params = [], []
        if contributor_did:
            conditions.append("contributor_did=?")
            params.append(contributor_did)
        if contribution_type:
            conditions.append("contribution_type=?")
            params.append(contribution_type)
        if verified is not None:
            conditions.append("verified=?")
            params.append(verified)
        return self.list_all(
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )

    def get_latest_by_did_and_type(self, contributor_did: str, contribution_type: str):
        row = self.db.execute(
            f"SELECT {', '.join(self.cols)} FROM {self.table_name} WHERE contributor_did=? AND contribution_type=? ORDER BY id DESC LIMIT 1",
            (contributor_did, contribution_type),
        ).fetchone()
        return dict(row) if row else None

    def get_recent(self, limit: int = 5):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]


class FederatedRoundsRepository(BaseRepository):
    """联邦学习轮次表。"""

    def __init__(self, db):
        super().__init__(db, "federated_rounds", TABLE_FEDERATED_ROUNDS_COLS)


class FederatedNodesRepository(BaseRepository):
    """联邦节点表。"""

    def __init__(self, db):
        super().__init__(db, "federated_nodes", TABLE_FEDERATED_NODES_COLS)

    def get_by_node_id(self, node_id):
        row = self.db.execute(
            f"SELECT {', '.join(self.cols)} FROM {self.table_name} WHERE node_id=?",
            (node_id,),
        ).fetchone()
        return dict(row) if row else None

    def get_all(self):
        return super().get_all()


class AuditChainBlocksRepository(BaseRepository):
    """审计链区块表。"""

    def __init__(self, db):
        super().__init__(db, "audit_chain_blocks", TABLE_AUDIT_CHAIN_BLOCKS_COLS)

    def get_latest(self):
        row = self.db.execute(f"SELECT {', '.join(self.cols)} FROM {self.table_name} ORDER BY id DESC LIMIT 1").fetchone()
        return dict(row) if row else None

    def get_chain(self, node_id: str, limit: int = 100):
        rows = self.db.execute(
            f"SELECT {', '.join(self.cols)} FROM {self.table_name} WHERE node_id=? ORDER BY id DESC LIMIT ?",
            (node_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


class BenchmarkReportsRepository(BaseRepository):
    """基准测试报告表。"""

    def __init__(self, db):
        super().__init__(db, "benchmark_reports", TABLE_BENCHMARK_REPORTS_COLS)

    def list_by_report_type(self, report_type=None) -> list:
        placeholders = ", ".join(self.cols)
        where = ""
        params = []
        if report_type:
            where = "WHERE report_type = ?"
            params.append(report_type)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name}{where} ORDER BY created_at DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]
