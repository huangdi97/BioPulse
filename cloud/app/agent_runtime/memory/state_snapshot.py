"""Runtime state snapshot persistence with incremental diffs."""

from datetime import datetime, timedelta

from cloud.app.agent_runtime.memory.snapshot_diff import (
    _apply_diff,
    _compute_diff,
    _deserialize,
    _is_anchor_step,
    _serialize,
)


def ensure_snapshot_table(db) -> None:
    """确保快照表存在，不存在则创建。"""
    db.execute(
        "CREATE TABLE IF NOT EXISTS agent_runtime_snapshots ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "trace_id TEXT NOT NULL, "
        "step INTEGER NOT NULL, "
        "state_json TEXT NOT NULL, "
        "snapshot_type TEXT DEFAULT 'full', "
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
        "expires_at TIMESTAMP"
        ")"
    )
    db.execute("CREATE INDEX IF NOT EXISTS idx_agent_runtime_snapshots_trace_step ON agent_runtime_snapshots(trace_id, step)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_agent_runtime_snapshots_type ON agent_runtime_snapshots(trace_id, snapshot_type)")
    try:
        db.execute("ALTER TABLE agent_runtime_snapshots ADD COLUMN snapshot_type TEXT DEFAULT 'full'")
    except Exception:
        pass
    db.commit()


def _row_to_snapshot(row) -> dict | None:
    if row is None:
        return None
    state = _deserialize(row["state_json"])
    return {
        "id": row["id"],
        "trace_id": row["trace_id"],
        "step": row["step"],
        "state": state,
        "state_json": row["state_json"],
        "snapshot_type": row.get("snapshot_type", "full"),
        "created_at": row["created_at"],
        "expires_at": row["expires_at"],
    }


def save_snapshot(db, trace_id: str, step: int, state_dict: dict) -> int:
    """保存运行时状态快照。step>0 时保存 diff（与上一步差异），每 5 步存全量锚点。"""
    ensure_snapshot_table(db)
    expires_at = datetime.now() + timedelta(days=7)
    is_anchor = _is_anchor_step(step)
    if is_anchor:
        serialized = _serialize(state_dict)
        cur = db.execute(
            "INSERT INTO agent_runtime_snapshots (trace_id, step, state_json, snapshot_type, expires_at) VALUES (?, ?, ?, 'full', ?)",
            (trace_id, step, serialized, expires_at.isoformat()),
        )
    else:
        prev = db.execute(
            "SELECT * FROM agent_runtime_snapshots WHERE trace_id=? AND step=? ORDER BY id DESC LIMIT 1",
            (trace_id, step - 1),
        ).fetchone()
        if prev:
            prev_state = _deserialize(prev["state_json"])
            if prev.get("snapshot_type") == "diff":
                prev_full_row = db.execute(
                    "SELECT * FROM agent_runtime_snapshots WHERE trace_id=? AND snapshot_type='full' AND step<=? ORDER BY step DESC LIMIT 1",
                    (trace_id, step - 1),
                ).fetchone()
                if prev_full_row:
                    prev_state = _deserialize(prev_full_row["state_json"])
            diff = _compute_diff(state_dict, prev_state)
            serialized = _serialize(diff)
        else:
            serialized = _serialize(state_dict)
        cur = db.execute(
            "INSERT INTO agent_runtime_snapshots (trace_id, step, state_json, snapshot_type, expires_at) VALUES (?, ?, ?, 'diff', ?)",
            (trace_id, step, serialized, expires_at.isoformat()),
        )
    db.commit()
    return cur.lastrowid


def load_latest_snapshot(db, trace_id: str) -> dict | None:
    """加载指定 trace 的最新快照，从全量锚点 + 逐层 diff 重建。"""
    ensure_snapshot_table(db)
    latest = db.execute(
        "SELECT * FROM agent_runtime_snapshots WHERE trace_id=? ORDER BY step DESC, id DESC LIMIT 1",
        (trace_id,),
    ).fetchone()
    if not latest:
        return None
    target_step = latest["step"]
    anchor = db.execute(
        "SELECT * FROM agent_runtime_snapshots WHERE trace_id=? AND snapshot_type='full' AND step<=? ORDER BY step DESC LIMIT 1",
        (trace_id, target_step),
    ).fetchone()
    if not anchor:
        return _row_to_snapshot(latest)
    state = _deserialize(anchor["state_json"])
    diffs = db.execute(
        "SELECT * FROM agent_runtime_snapshots WHERE trace_id=? AND snapshot_type='diff' AND step>? AND step<=? ORDER BY step ASC",
        (trace_id, anchor["step"], target_step),
    ).fetchall()
    for d in diffs:
        diff_data = _deserialize(d["state_json"])
        state = _apply_diff(state, diff_data)
    return {
        "id": latest["id"],
        "trace_id": latest["trace_id"],
        "step": latest["step"],
        "state": state,
        "state_json": _serialize(state),
        "snapshot_type": latest.get("snapshot_type", "full"),
        "created_at": latest["created_at"],
        "expires_at": latest["expires_at"],
    }


def load_snapshot(db, trace_id: str, step: int) -> dict | None:
    """加载指定 trace 和 step 的快照。"""
    ensure_snapshot_table(db)
    row = db.execute(
        "SELECT * FROM agent_runtime_snapshots WHERE trace_id=? AND step=? ORDER BY id DESC LIMIT 1",
        (trace_id, step),
    ).fetchone()
    if not row:
        return None
    snapshot_type = row.get("snapshot_type", "full")
    if snapshot_type == "full":
        return _row_to_snapshot(row)
    anchor = db.execute(
        "SELECT * FROM agent_runtime_snapshots WHERE trace_id=? AND snapshot_type='full' AND step<=? ORDER BY step DESC LIMIT 1",
        (trace_id, step),
    ).fetchone()
    if not anchor:
        return _row_to_snapshot(row)
    state = _deserialize(anchor["state_json"])
    diffs = db.execute(
        "SELECT * FROM agent_runtime_snapshots WHERE trace_id=? AND snapshot_type='diff' AND step>? AND step<=? ORDER BY step ASC",
        (trace_id, anchor["step"], step),
    ).fetchall()
    for d in diffs:
        diff_data = _deserialize(d["state_json"])
        state = _apply_diff(state, diff_data)
    return {
        "id": row["id"],
        "trace_id": row["trace_id"],
        "step": row["step"],
        "state": state,
        "state_json": _serialize(state),
        "snapshot_type": snapshot_type,
        "created_at": row["created_at"],
        "expires_at": row["expires_at"],
    }


def delete_expired_snapshots(db) -> int:
    """删除已过期的快照记录。"""
    ensure_snapshot_table(db)
    now = datetime.now().isoformat()
    cur = db.execute("DELETE FROM agent_runtime_snapshots WHERE expires_at IS NOT NULL AND expires_at < ?", (now,))
    db.commit()
    return cur.rowcount


def recover(db, trace_id: str | None = None) -> list[dict]:
    """扫描未完成的 checkpoint 并返回可恢复的快照列表。

    返回状态为 'interrupted' 或 'active' 且 expires_at 未过期的快照。
    """
    ensure_snapshot_table(db)
    now = datetime.now().isoformat()
    if trace_id:
        rows = db.execute(
            "SELECT * FROM agent_runtime_snapshots WHERE trace_id=? AND (status='interrupted' OR status='active') "
            "AND (expires_at IS NULL OR expires_at > ?) ORDER BY step DESC LIMIT 1",
            (trace_id, now),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM agent_runtime_snapshots WHERE (status='interrupted' OR status='active') "
            "AND (expires_at IS NULL OR expires_at > ?) ORDER BY created_at DESC",
            (now,),
        ).fetchall()
    return [_row_to_snapshot(r) for r in rows]


class StateSnapshot:
    """Compatibility wrapper around runtime snapshots and the old agent snapshot table."""

    def __init__(self, agent_db):
        self._agent_db = agent_db
        ensure_snapshot_table(agent_db)
        self._create_legacy_table()

    def _create_legacy_table(self):
        self._agent_db.execute(
            "CREATE TABLE IF NOT EXISTS agent_state_snapshots ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "agent_id TEXT NOT NULL, "
            "step_id INTEGER DEFAULT 0, "
            "plan_json TEXT DEFAULT '[]', "
            "results_json TEXT DEFAULT '[]', "
            "context_json TEXT DEFAULT '{}', "
            "created_at TEXT DEFAULT CURRENT_TIMESTAMP, "
            "status TEXT DEFAULT 'active'"
            ")"
        )
        self._agent_db.execute("CREATE INDEX IF NOT EXISTS idx_state_snapshots_agent ON agent_state_snapshots(agent_id)")
        self._agent_db.execute("CREATE INDEX IF NOT EXISTS idx_state_snapshots_status ON agent_state_snapshots(status)")
        self._agent_db.commit()

    def save_runtime(self, trace_id, step, state_dict):
        """保存运行时快照。"""
        return save_snapshot(self._agent_db, trace_id, step, state_dict)

    def load_runtime_latest(self, trace_id):
        """加载最新运行时快照。"""
        return load_latest_snapshot(self._agent_db, trace_id)

    def load_runtime(self, trace_id, step):
        """加载指定 step 的运行时快照。"""
        return load_snapshot(self._agent_db, trace_id, step)

    def save(self, agent_id, step_id, plan, results, context, status="active"):
        """保存传统格式的状态快照。"""
        cur = self._agent_db.execute(
            "INSERT INTO agent_state_snapshots "
            "(agent_id, step_id, plan_json, results_json, context_json, created_at, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                agent_id,
                step_id,
                _serialize(plan),
                _serialize(results),
                _serialize(context),
                datetime.now().isoformat(),
                status,
            ),
        )
        self._agent_db.commit()
        self._cleanup(agent_id)
        return cur.lastrowid

    def load(self, snapshot_id):
        """加载传统格式的状态快照。"""
        row = self._agent_db.execute("SELECT * FROM agent_state_snapshots WHERE id=?", (snapshot_id,)).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "agent_id": row["agent_id"],
            "step_id": row["step_id"],
            "plan": _deserialize(row["plan_json"]),
            "results": _deserialize(row["results_json"]),
            "context": _deserialize(row["context_json"]),
            "created_at": row["created_at"],
            "status": row["status"],
        }

    def list_snapshots(self, agent_id, limit=10):
        """列出指定 agent 的快照列表。"""
        rows = self._agent_db.execute(
            "SELECT id, agent_id, step_id, created_at, status FROM agent_state_snapshots WHERE agent_id=? ORDER BY id DESC LIMIT ?",
            (agent_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_latest(self, agent_id):
        """获取指定 agent 的最新活跃快照。"""
        row = self._agent_db.execute(
            "SELECT * FROM agent_state_snapshots WHERE agent_id=? AND status='active' ORDER BY id DESC LIMIT 1",
            (agent_id,),
        ).fetchone()
        if not row:
            return None
        return self.load(row["id"])

    def mark_rolled_back(self, snapshot_id):
        """将快照标记为已回滚。"""
        self._agent_db.execute("UPDATE agent_state_snapshots SET status='rolled_back' WHERE id=?", (snapshot_id,))
        self._agent_db.commit()

    def _cleanup(self, agent_id):
        self._agent_db.execute(
            "DELETE FROM agent_state_snapshots WHERE agent_id=? AND id NOT IN ("
            "SELECT id FROM agent_state_snapshots WHERE agent_id=? ORDER BY id DESC LIMIT 50"
            ")",
            (agent_id, agent_id),
        )
        self._agent_db.commit()


SnapshotManager = StateSnapshot
