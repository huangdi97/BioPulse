from cloud.app.agent_runtime.runtime_llm.config import estimate_complexity, estimate_token_count


def test_estimate_token_count_empty():
    assert estimate_token_count([]) == 0


def test_estimate_token_count_simple():
    msgs = [{"role": "user", "content": "hello world"}]
    count = estimate_token_count(msgs)
    assert count > 0


def test_estimate_complexity_low():
    msgs = [{"role": "user", "content": "hi"}]
    assert estimate_complexity(msgs) == 1


def test_estimate_complexity_high():
    msgs = [{"role": "user", "content": "x" * 6000}]
    assert estimate_complexity(msgs) >= 3


def test_estimate_complexity_max():
    msgs = [{"role": "user", "content": "x" * 12000}]
    assert estimate_complexity(msgs) == 5
