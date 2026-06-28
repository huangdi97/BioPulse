import json
from unittest.mock import MagicMock, patch

from cloud.app.agent_runtime.memory.world_model import (
    WorldModelLoop,
    get_world_model,
)


def test_world_model_singleton():
    instance1 = get_world_model()
    instance2 = get_world_model()
    assert instance1 is instance2


@patch("cloud.app.agent_runtime.memory.world_model.get_shared_state")
def test_full_scan_empty_state(mock_get_ss):
    mock_ss = MagicMock()
    mock_ss._entries = []
    mock_get_ss.return_value = mock_ss

    wm = WorldModelLoop()
    wm._full_scan()


def test_parse_llm_output_valid():
    reply = json.dumps(
        [
            {"pattern": "test-pattern", "description": "a pattern", "confidence": 0.8},
        ]
    )
    result = WorldModelLoop._parse_llm_output(reply, [])
    assert len(result) == 1
    assert result[0]["pattern"] == "test-pattern"
    assert result[0]["confidence"] == 0.8


def test_parse_llm_output_invalid():
    result = WorldModelLoop._parse_llm_output("not valid json", [])
    assert result == []
