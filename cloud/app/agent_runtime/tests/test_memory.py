"""Tests for Memory (AgentBrain)."""

from unittest.mock import MagicMock

from cloud.app.agent_runtime.memory import Memory


def _make_memory():
    db = MagicMock()
    return Memory(db), db


def test_memory_init():
    """test memory init."""
    mem, _ = _make_memory()
    assert mem is not None
    assert mem._agent_db is not None


def test_memory_set_and_get_str():
    """test memory set and get str."""
    mem, db = _make_memory()
    cursor = MagicMock()
    cursor.fetchone.return_value = {"value": "hello", "value_type": "str"}
    db.execute.return_value = cursor

    mem.set("agent_1", "greeting", "hello")
    db.execute.assert_called()
    db.commit.assert_called_once()

    result = mem.get("agent_1", "greeting")
    assert result == "hello"


def test_memory_get_empty():
    """test memory get empty returns None."""
    mem, db = _make_memory()
    cursor = MagicMock()
    cursor.fetchone.return_value = None
    db.execute.return_value = cursor

    result = mem.get("agent_1", "nonexistent")
    assert result is None


def test_memory_set_and_get_int():
    """test memory set and get int."""
    mem, db = _make_memory()
    cursor = MagicMock()
    cursor.fetchone.return_value = {"value": "42", "value_type": "int"}
    db.execute.return_value = cursor

    mem.set("agent_1", "count", 42)
    result = mem.get("agent_1", "count")
    assert result == 42


def test_memory_set_and_get_float():
    """test memory set and get float."""
    mem, db = _make_memory()
    cursor = MagicMock()
    cursor.fetchone.return_value = {"value": "3.14", "value_type": "float"}
    db.execute.return_value = cursor

    mem.set("agent_1", "pi", 3.14)
    result = mem.get("agent_1", "pi")
    assert result == 3.14


def test_memory_set_and_get_json():
    """test memory set and get json."""
    mem, db = _make_memory()
    cursor = MagicMock()
    cursor.fetchone.return_value = {"value": '{"a":1}', "value_type": "json"}
    db.execute.return_value = cursor

    mem.set("agent_1", "data", {"a": 1})
    result = mem.get("agent_1", "data")
    assert result == {"a": 1}


def test_memory_delete():
    """test memory delete."""
    mem, db = _make_memory()
    mem.delete("agent_1", "greeting")
    db.execute.assert_called_once()
    db.commit.assert_called_once()
