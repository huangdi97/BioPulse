"""Tests for SharedState / SharedStateEntry."""

import threading
import time

import pytest

from cloud.app.agent_runtime.shared_state import SharedState, SharedStateEntry, _validate_namespace


def _make_entry(**overrides) -> SharedStateEntry:
    defaults = dict(
        namespace="compliance",
        key="test.key",
        value="val",
        confidence=0.8,
        agent_key="compliance_monitor",
        timestamp="",
        version=1,
        evidence=["src1"],
    )
    defaults.update(overrides)
    return SharedStateEntry(**defaults)


def test_write_and_read():
    ss = SharedState()
    e = _make_entry()
    ss.write(e, caller_agent_key="compliance_monitor")
    results = ss.read(namespace="compliance")
    assert len(results) == 1
    assert results[0].key == "test.key"
    assert results[0].version > 0
    assert results[0].timestamp != ""


def test_read_filter_by_key_prefix():
    ss = SharedState()
    ss.write(_make_entry(key="华北区.评分"), caller_agent_key="compliance_monitor")
    ss.write(_make_entry(key="华东区.评分"), caller_agent_key="compliance_monitor")
    results = ss.read(namespace="compliance", key="华北")
    assert len(results) == 1
    assert results[0].key == "华北区.评分"


def test_read_filter_by_confidence():
    ss = SharedState()
    ss.write(_make_entry(key="a", confidence=0.5), caller_agent_key="compliance_monitor")
    ss.write(_make_entry(key="b", confidence=0.9), caller_agent_key="compliance_monitor")
    results = ss.read(namespace="compliance", min_confidence=0.8)
    assert len(results) == 1
    assert results[0].key == "b"


def test_namespace_mismatch_raises():
    with pytest.raises(PermissionError, match="无权写入"):
        _validate_namespace("compliance_monitor", "analysis.stats")


def test_namespace_match_passes():
    _validate_namespace("compliance_monitor", "compliance.stats")


def test_low_confidence_warns(caplog):
    import logging

    caplog.set_level(logging.WARNING)
    ss = SharedState()
    ss.write(_make_entry(confidence=0.2), caller_agent_key="compliance_monitor")
    assert "Low confidence" in caplog.text


def test_empty_evidence_warns(caplog):
    import logging

    caplog.set_level(logging.WARNING)
    ss = SharedState()
    ss.write(_make_entry(evidence=[]), caller_agent_key="compliance_monitor")
    assert "Empty evidence" in caplog.text


def test_watch_notifies():
    ss = SharedState()
    received = []

    def collector():
        for entry in ss.watch("compliance.*"):
            received.append(entry)
            break

    t = threading.Thread(target=collector, daemon=True)
    t.start()
    time.sleep(0.05)
    ss.write(_make_entry(), caller_agent_key="compliance_monitor")
    time.sleep(0.05)
    assert len(received) == 1
    assert received[0].key == "test.key"


def test_watch_pattern_no_match():
    ss = SharedState()
    received = []

    def collector():
        for entry in ss.watch("analysis.*"):
            received.append(entry)
            break

    t = threading.Thread(target=collector, daemon=True)
    t.start()
    time.sleep(0.05)
    ss.write(_make_entry(), caller_agent_key="compliance_monitor")
    time.sleep(0.05)
    assert len(received) == 0
