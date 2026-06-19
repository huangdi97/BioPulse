"""Tests for TrajectoryRecorder replay."""

from cloud.app.agent_runtime.trajectory_recorder import TrajectoryRecorder


def test_replay_known_trajectory(tmp_path):
    """test replaying a known trajectory produces expected records."""
    recorder = TrajectoryRecorder(base_dir=str(tmp_path))
    tid = "traj-001"

    recorder.record_input(tid, {"query": "hello"})
    recorder.record_step(tid, {"tool": "search", "result": "found"})
    recorder.record_final(tid, {"answer": "world"})

    records = recorder.load_trajectory(tid)
    assert len(records) == 3
    assert records[0]["type"] == "input"
    assert records[0]["data"] == {"query": "hello"}
    assert records[1]["type"] == "step"
    assert records[1]["data"] == {"tool": "search", "result": "found"}
    assert records[2]["type"] == "final"
    assert records[2]["data"] == {"answer": "world"}
    for r in records:
        assert r["trajectory_id"] == tid
        assert "timestamp" in r


def test_replay_consistency(tmp_path):
    """test that replay order matches recording order exactly."""
    recorder = TrajectoryRecorder(base_dir=str(tmp_path))
    tid = "traj-002"

    steps = [
        {"type": "input", "data": {"x": 1}},
        {"type": "step", "data": {"intermediate": "a"}},
        {"type": "step", "data": {"intermediate": "b"}},
        {"type": "step", "data": {"intermediate": "c"}},
        {"type": "final", "data": {"result": 42}},
    ]

    for s in steps:
        if s["type"] == "input":
            recorder.record_input(tid, s["data"])
        elif s["type"] == "step":
            recorder.record_step(tid, s["data"])
        elif s["type"] == "final":
            recorder.record_final(tid, s["data"])

    records = recorder.load_trajectory(tid)
    assert len(records) == 5
    for recorded, expected in zip(records, steps):
        assert recorded["type"] == expected["type"]
        assert recorded["data"] == expected["data"]
