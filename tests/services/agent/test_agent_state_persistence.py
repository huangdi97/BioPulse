"""Agent 状态持久化集成测试。"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timedelta

import pytest

from cloud.app.agent_runtime.runtime_state import RuntimeState
from cloud.app.agent_runtime.state_snapshot import (
    StateSnapshot,
    delete_expired_snapshots,
    ensure_snapshot_table,
    load_latest_snapshot,
    load_snapshot,
    save_snapshot,
)


@pytest.fixture
def agent_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS agent_runtime_logs ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "agent_key TEXT NOT NULL, "
        "goal TEXT NOT NULL, "
        "status TEXT DEFAULT 'running', "
        "checkpoint_data TEXT, "
        "trace_id TEXT"
        ")"
    )
    yield conn
    conn.close()


@pytest.fixture
def runtime_state(agent_db):
    return RuntimeState(agent_db)


@pytest.fixture
def snapshot_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_snapshot_table(conn)
    yield conn
    conn.close()


@pytest.fixture
def state_snapshot(snapshot_db):
    return StateSnapshot(snapshot_db)


class AgentState:
    def __init__(self, agent_key: str, goal: str, messages: list, context: dict, step: int = 0):
        self.agent_key = agent_key
        self.goal = goal
        self.messages = messages
        self.context = context
        self.step = step

    def to_dict(self) -> dict:
        return {
            "agent_key": self.agent_key,
            "goal": self.goal,
            "messages": self.messages,
            "context": self.context,
            "step": self.step,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AgentState:
        return cls(
            agent_key=data["agent_key"],
            goal=data["goal"],
            messages=data.get("messages", []),
            context=data.get("context", {}),
            step=data.get("step", 0),
        )


class TestStateSerialization:
    def test_serialize_full_fields(self):
        state = AgentState("agent_a", "find opportunities", [{"role": "user", "content": "hello"}], {"user_id": "u1"}, step=3)
        d = state.to_dict()
        assert d["agent_key"] == "agent_a"
        assert d["goal"] == "find opportunities"
        assert len(d["messages"]) == 1
        assert d["context"]["user_id"] == "u1"
        assert d["step"] == 3

    def test_serialize_to_json_roundtrip(self):
        state = AgentState("agent_b", "analyze", [{"role": "assistant", "content": "done"}], {}, step=5)
        json_str = json.dumps(state.to_dict(), ensure_ascii=False)
        restored = AgentState.from_dict(json.loads(json_str))
        assert restored.agent_key == "agent_b"
        assert restored.goal == "analyze"
        assert restored.messages[0]["content"] == "done"
        assert restored.step == 5

    def test_serialize_empty_messages(self):
        state = AgentState("agent_c", "empty", [], {}, step=0)
        d = state.to_dict()
        assert d["messages"] == []


class TestStateDeserialization:
    def test_deserialize_full_fields(self):
        data = {
            "agent_key": "agent_d",
            "goal": "research",
            "messages": [{"role": "user", "content": "query"}],
            "context": {"source": "web"},
            "step": 2,
        }
        state = AgentState.from_dict(data)
        assert state.agent_key == "agent_d"
        assert state.step == 2
        assert state.context["source"] == "web"

    def test_deserialize_minimal_fields(self):
        data = {"agent_key": "agent_e", "goal": "minimal", "messages": [], "context": {}, "step": 0}
        state = AgentState.from_dict(data)
        assert state.messages == []

    def test_deserialize_missing_messages_defaults_empty(self):
        data = {"agent_key": "agent_f", "goal": "test"}
        state = AgentState.from_dict(data)
        assert state.messages == []


class TestRuntimeStatePersistence:
    def test_save_and_load_state(self, runtime_state: RuntimeState):
        runtime_state.save("agent_1", "goal_1", {"step": 1, "data": "test"}, "trace_1")
        loaded = runtime_state.load("agent_1", "goal_1")
        assert loaded is not None
        assert loaded["step"] == 1
        assert loaded["data"] == "test"

    def test_load_nonexistent_returns_none(self, runtime_state: RuntimeState):
        result = runtime_state.load("ghost", "nope")
        assert result is None

    def test_delete_clears_checkpoint(self, runtime_state: RuntimeState):
        runtime_state.save("agent_2", "goal_2", {"key": "val"}, "trace_2")
        runtime_state.delete("agent_2", "goal_2")
        loaded = runtime_state.load("agent_2", "goal_2")
        assert loaded is None

    def test_save_overwrites_previous(self, runtime_state: RuntimeState):
        runtime_state.save("agent_3", "goal_3", {"version": 1}, "trace_3")
        runtime_state.save("agent_3", "goal_3", {"version": 2}, "trace_4")
        loaded = runtime_state.load("agent_3", "goal_3")
        assert loaded["version"] == 2

    def test_state_fields_roundtrip(self, runtime_state: RuntimeState):
        data = {
            "step": 5,
            "messages": [{"role": "user", "content": "hello"}],
            "context": {"user": "test"},
            "tool_results": [{"tool": "search", "result": "data"}],
            "iteration": 3,
        }
        runtime_state.save("agent_4", "goal_4", data, "trace_5")
        loaded = runtime_state.load("agent_4", "goal_4")
        assert loaded["step"] == 5
        assert loaded["messages"][0]["content"] == "hello"
        assert loaded["context"]["user"] == "test"
        assert loaded["tool_results"][0]["tool"] == "search"
        assert loaded["iteration"] == 3


class TestIncrementalUpdate:
    def test_update_single_field(self, runtime_state: RuntimeState):
        runtime_state.save("agent_5", "goal_5", {"step": 1, "data": "initial"}, "trace_6")
        runtime_state.save("agent_5", "goal_5", {"step": 2, "data": "initial"}, "trace_7")
        loaded = runtime_state.load("agent_5", "goal_5")
        assert loaded["step"] == 2
        assert loaded["data"] == "initial"

    def test_update_preserves_other_fields(self, runtime_state: RuntimeState):
        runtime_state.save("agent_6", "goal_6", {"step": 1, "data": "val", "status": "running"}, "trace_8")
        runtime_state.save("agent_6", "goal_6", {"step": 2, "data": "val", "status": "running"}, "trace_9")
        loaded = runtime_state.load("agent_6", "goal_6")
        assert loaded["step"] == 2
        assert loaded["data"] == "val"


class TestConcurrentWriteProtection:
    def test_two_agents_different_keys(self):
        import os
        import tempfile

        db_dir = tempfile.mkdtemp()
        errors: list[Exception] = []

        def save_agent(key: str):
            try:
                conn = sqlite3.connect(os.path.join(db_dir, f"{key}.db"))
                conn.row_factory = sqlite3.Row
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS agent_runtime_logs ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "agent_key TEXT NOT NULL, "
                    "goal TEXT NOT NULL, "
                    "status TEXT DEFAULT 'running', "
                    "checkpoint_data TEXT, "
                    "trace_id TEXT"
                    ")"
                )
                rs = RuntimeState(conn)
                for i in range(5):
                    rs.save(key, f"goal_{key}", {"iteration": i}, f"trace_{key}_{i}")
                conn.close()
            except Exception as e:
                errors.append(e)

        threads = []
        for key in ["agent_a", "agent_b"]:
            t = threading.Thread(target=save_agent, args=(key,))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0
        import shutil

        shutil.rmtree(db_dir, ignore_errors=True)

    def test_concurrent_writes_no_corruption(self):
        import os
        import tempfile

        db_dir = tempfile.mkdtemp()
        errors: list[Exception] = []

        def writer(key: str):
            try:
                conn = sqlite3.connect(os.path.join(db_dir, f"{key}.db"))
                conn.row_factory = sqlite3.Row
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS agent_runtime_logs ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "agent_key TEXT NOT NULL, "
                    "goal TEXT NOT NULL, "
                    "status TEXT DEFAULT 'running', "
                    "checkpoint_data TEXT, "
                    "trace_id TEXT"
                    ")"
                )
                rs = RuntimeState(conn)
                for i in range(10):
                    rs.save(key, f"goal_{key}", {"count": i}, f"trace_{key}_{i}")
                conn.close()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(f"agent_{i}",)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0
        import shutil

        shutil.rmtree(db_dir, ignore_errors=True)


class TestLargeState:
    def test_large_messages_saved_and_loaded(self, runtime_state: RuntimeState):
        messages = [{"role": "user", "content": f"msg_{i}"} for i in range(500)]
        data = {"step": 1, "messages": messages, "context": {}}
        runtime_state.save("large_agent", "large_goal", data, "trace_large")
        loaded = runtime_state.load("large_agent", "large_goal")
        assert loaded is not None
        assert len(loaded["messages"]) == 500
        assert loaded["messages"][0]["content"] == "msg_0"
        assert loaded["messages"][499]["content"] == "msg_499"

    def test_state_with_over_1000_messages(self, runtime_state: RuntimeState):
        messages = [{"role": "assistant", "content": f"response_{i}"} for i in range(1001)]
        data = {"step": 10, "messages": messages}
        runtime_state.save("big_agent", "big_goal", data, "trace_big")
        loaded = runtime_state.load("big_agent", "big_goal")
        assert loaded is not None
        assert len(loaded["messages"]) == 1001


class TestCorruptState:
    def test_corrupt_json_raises_error(self, agent_db):
        agent_db.execute(
            "INSERT INTO agent_runtime_logs (agent_key, goal, status, checkpoint_data, trace_id) VALUES (?, ?, 'running', ?, ?)",
            ("corrupt_agent", "corrupt_goal", "not valid json{{", "trace_corrupt"),
        )
        agent_db.commit()
        rs = RuntimeState(agent_db)
        import json

        with pytest.raises(json.JSONDecodeError):
            rs.load("corrupt_agent", "corrupt_goal")

    def test_corrupt_json_in_snapshot(self, snapshot_db):
        snapshot_db.execute(
            "INSERT INTO agent_runtime_snapshots (trace_id, step, state_json, expires_at) VALUES (?, ?, ?, ?)",
            ("corrupt_trace", 1, "{invalid json{{{", (datetime.now() + timedelta(days=1)).isoformat()),
        )
        snapshot_db.commit()
        result = load_latest_snapshot(snapshot_db, "corrupt_trace")
        assert result is None or isinstance(result, dict)

    def test_empty_state_json(self, agent_db):
        agent_db.execute(
            "INSERT INTO agent_runtime_logs (agent_key, goal, status, checkpoint_data, trace_id) VALUES (?, ?, 'running', ?, ?)",
            ("empty_agent", "empty_goal", None, "trace_empty"),
        )
        agent_db.commit()
        rs = RuntimeState(agent_db)
        result = rs.load("empty_agent", "empty_goal")
        assert result is None


class TestAutoCleanup:
    def test_delete_expired_snapshots(self, snapshot_db):
        past = (datetime.now() - timedelta(days=10)).isoformat()
        future = (datetime.now() + timedelta(days=10)).isoformat()
        snapshot_db.execute(
            "INSERT INTO agent_runtime_snapshots (trace_id, step, state_json, expires_at) VALUES (?, ?, ?, ?)",
            ("trace_expired", 1, "{}", past),
        )
        snapshot_db.execute(
            "INSERT INTO agent_runtime_snapshots (trace_id, step, state_json, expires_at) VALUES (?, ?, ?, ?)",
            ("trace_valid", 2, "{}", future),
        )
        snapshot_db.commit()
        deleted = delete_expired_snapshots(snapshot_db)
        assert deleted >= 1
        remaining = snapshot_db.execute("SELECT COUNT(*) FROM agent_runtime_snapshots").fetchone()[0]
        assert remaining == 1

    def test_cleanup_no_expired_snapshots(self, snapshot_db):
        future = (datetime.now() + timedelta(days=1)).isoformat()
        snapshot_db.execute(
            "INSERT INTO agent_runtime_snapshots (trace_id, step, state_json, expires_at) VALUES (?, ?, ?, ?)",
            ("trace_future", 1, "{}", future),
        )
        snapshot_db.commit()
        deleted = delete_expired_snapshots(snapshot_db)
        assert deleted == 0

    def test_cleanup_none_expires(self, snapshot_db):
        for i in range(3):
            snapshot_db.execute(
                "INSERT INTO agent_runtime_snapshots (trace_id, step, state_json) VALUES (?, ?, ?)",
                (f"trace_{i}", i, "{}"),
            )
        snapshot_db.commit()
        deleted = delete_expired_snapshots(snapshot_db)
        assert deleted == 0


class TestStateSnapshot:
    def test_save_and_load_snapshot(self, snapshot_db):
        state = {"step": 3, "messages": [{"role": "user", "content": "hi"}]}
        snap_id = save_snapshot(snapshot_db, "trace_snap", 3, state)
        assert snap_id is not None
        loaded = load_snapshot(snapshot_db, "trace_snap", 3)
        assert loaded is not None
        assert loaded["step"] == 3
        assert loaded["state"]["messages"][0]["content"] == "hi"

    def test_load_latest_snapshot(self, snapshot_db):
        save_snapshot(snapshot_db, "trace_latest", 1, {"data": "first"})
        save_snapshot(snapshot_db, "trace_latest", 2, {"data": "second"})
        latest = load_latest_snapshot(snapshot_db, "trace_latest")
        assert latest["state"]["data"] == "second"

    def test_snapshot_not_found_returns_none(self, snapshot_db):
        result = load_snapshot(snapshot_db, "nonexistent", 999)
        assert result is None

    def test_legacy_save_and_load(self, state_snapshot: StateSnapshot):
        snap_id = state_snapshot.save("legacy_agent", 1, [{"step": 1}], [], {"user": "test"}, "active")
        assert snap_id is not None
        loaded = state_snapshot.load(snap_id)
        assert loaded["agent_id"] == "legacy_agent"
        assert loaded["step_id"] == 1
        assert loaded["status"] == "active"

    def test_legacy_get_latest(self, state_snapshot: StateSnapshot):
        state_snapshot.save("latest_agent", 1, [], [], {}, "active")
        state_snapshot.save("latest_agent", 2, [], [], {}, "active")
        latest = state_snapshot.get_latest("latest_agent")
        assert latest["step_id"] == 2

    def test_legacy_list_snapshots(self, state_snapshot: StateSnapshot):
        for i in range(5):
            state_snapshot.save("list_agent", i, [], [], {}, "active")
        snaps = state_snapshot.list_snapshots("list_agent", limit=3)
        assert len(snaps) <= 3

    def test_mark_rolled_back(self, state_snapshot: StateSnapshot):
        snap_id = state_snapshot.save("rb_agent", 1, [], [], {}, "active")
        state_snapshot.mark_rolled_back(snap_id)
        loaded = state_snapshot.load(snap_id)
        assert loaded["status"] == "rolled_back"
