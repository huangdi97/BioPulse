import json
import sqlite3

import pytest

from cloud.app.agent_runtime.cost_governor import CostGovernor
from cloud.app.agent_runtime.runtime_llm import RuntimeLLM


def _connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _clear_runtime_tables(db_path):
    with _connect(db_path) as conn:
        for table in (
            "agent_runtime_snapshots",
            "agent_runtime_logs",
            "agent_runtime_approvals",
            "agent_state_snapshots",
            "agent_brains",
        ):
            conn.execute(f"DELETE FROM {table}")
        conn.commit()


def _decision(action, tool=None, params=None, reasoning="ok"):
    payload = {"action": action, "tool": tool, "params": params or {}, "reasoning": reasoning}
    return json.dumps(payload)


def _route_result(reply, prompt_tokens, completion_tokens, model_tier):
    cost = CostGovernor.estimate_cost(prompt_tokens, completion_tokens, model_tier)
    usage = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }
    return {
        "success": True,
        "data": {"data": {"reply": reply, "usage": usage}},
        "attempts": 1,
        "model_tier": model_tier,
        "cost": {
            "model_tier": model_tier,
            "input_tokens": prompt_tokens,
            "output_tokens": completion_tokens,
            "cost": round(cost, 9),
        },
    }


def _snapshot_states(db_path, trace_id):
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT step, state_json FROM agent_runtime_snapshots WHERE trace_id=? ORDER BY step, id",
            (trace_id,),
        ).fetchall()
    return [(row["step"], json.loads(row["state_json"])) for row in rows]


@pytest.fixture
def runtime_db(db_path, monkeypatch):
    import cloud.app.services.agent_runtime_service as service_mod

    monkeypatch.setattr(service_mod, "DB_PATH", db_path)
    _clear_runtime_tables(db_path)
    return db_path


def test_runtime_snapshots_rollback_and_cost_tracking(client, auth_token, runtime_db, monkeypatch):
    responses = [
        _route_result(
            _decision("call_tool", "agent_brain_get", {"key": "stage"}, "first tool"),
            100,
            50,
            "cloud_normal",
        ),
        _route_result(
            _decision("call_tool", "agent_brain_get", {"key": "stage"}, "second tool"),
            200,
            100,
            "cloud_agent",
        ),
        _route_result(_decision("complete", reasoning="initial done"), 300, 150, "local"),
        _route_result(_decision("complete", reasoning="rollback done"), 400, 200, "cloud_normal"),
    ]
    calls = []

    def fake_route(self, messages, temperature, force_level=None):
        calls.append(
            {
                "message_count": len(messages),
                "temperature": temperature,
                "force_level": force_level,
            }
        )
        return responses.pop(0)

    monkeypatch.setattr(RuntimeLLM, "_route_call", fake_route)
    headers = {"Authorization": f"Bearer {auth_token}"}

    execute_resp = client.post(
        "/agent/runtime/execute",
        json={
            "agent_key": "knowledge_worker",
            "goal": "exercise rollback snapshots",
            "context": {"case": "rollback"},
        },
        headers=headers,
    )

    assert execute_resp.status_code == 200, execute_resp.text
    execute_data = execute_resp.json()
    assert execute_data["status"] == "completed"
    assert execute_data["iterations"] == 3
    assert execute_data["tool_calls"] == 2

    trace_id = execute_data["metadata"]["trace_id"]
    initial_states = _snapshot_states(runtime_db, trace_id)
    assert [step for step, _state in initial_states] == [0, 1, 2]
    assert initial_states[0][1]["tool_calls_so_far"] == 1
    assert initial_states[1][1]["tool_calls_so_far"] == 2
    assert initial_states[2][1]["status"] == "completed"
    assert len(initial_states[1][1]["messages"]) == 6

    initial_cost = execute_data["metadata"]["cost"]
    assert initial_cost["call_count"] == 3
    assert [item["model_tier"] for item in initial_cost["step_costs"]] == [
        "cloud_normal",
        "cloud_agent",
        "local",
    ]
    assert initial_cost["total_input_tokens"] == 600
    assert initial_cost["total_output_tokens"] == 300
    assert initial_cost["total_cost"] == pytest.approx(0.000315)

    rollback_resp = client.post(
        f"/agent/runtime/rollback/{trace_id}",
        json={"step": 1},
        headers=headers,
    )

    assert rollback_resp.status_code == 200, rollback_resp.text
    rollback_data = rollback_resp.json()
    new_trace_id = rollback_data["trace_id"]
    assert new_trace_id != trace_id
    assert rollback_data["source_trace_id"] == trace_id
    assert rollback_data["step"] == 1
    assert rollback_data["tool_calls_so_far"] == 2
    assert rollback_data["messages"] == initial_states[1][1]["messages"]

    execution = rollback_data["execution"]
    assert execution["status"] == "completed"
    assert execution["result"] == "rollback done"
    assert execution["iterations"] == 3
    assert execution["metadata"]["trace_id"] == new_trace_id

    new_states = _snapshot_states(runtime_db, new_trace_id)
    assert [step for step, _state in new_states] == [1, 2]
    assert new_states[0][1]["status"] == "rolled_back"
    assert new_states[0][1]["rolled_back_from"] == trace_id
    assert new_states[0][1]["messages"] == initial_states[1][1]["messages"]
    assert new_states[1][1]["status"] == "completed"
    assert new_states[1][1]["tool_calls_so_far"] == 2

    rollback_cost = rollback_data["cost"]
    assert rollback_cost["call_count"] == 3
    assert rollback_cost["total_cost"] == pytest.approx(0.000495)
    assert execution["metadata"]["cost"] == rollback_cost
    assert [item["model_tier"] for item in rollback_cost["step_costs"]] == [
        "cloud_normal",
        "cloud_agent",
        "cloud_normal",
    ]
    assert rollback_cost["total_input_tokens"] == 700
    assert rollback_cost["total_output_tokens"] == 350
    assert calls[-1]["message_count"] == len(initial_states[1][1]["messages"])
    assert responses == []
