"""Tests for RateLimiter."""

from unittest.mock import patch

from cloud.app.agent_runtime.rate_limiter import RateLimiter, RateLimitExceeded


def test_rate_limiter_allows_within_limit():
    rl = RateLimiter()
    rl.set_limit("test_key", 5, 60)
    for _ in range(5):
        assert rl.check("test_key") is True


def test_rate_limiter_rejects_over_limit():
    rl = RateLimiter()
    rl.set_limit("test_key", 3, 60)
    for _ in range(3):
        rl.check("test_key")
    assert rl.check("test_key") is False


def test_rate_limiter_recovers_after_window():
    rl = RateLimiter()
    rl.set_limit("test_key", 2, 1)
    with patch("cloud.app.agent_runtime.rate_limiter.time.time", side_effect=[0, 0, 0, 1.1]):
        rl.check("test_key")
        rl.check("test_key")
        assert rl.check("test_key") is False
        assert rl.check("test_key") is True


def test_rate_limiter_check_or_raise():
    rl = RateLimiter()
    rl.set_limit("raise_key", 1, 60)
    rl.check_or_raise("raise_key")
    try:
        rl.check_or_raise("raise_key")
        assert False, "Expected RateLimitExceeded"
    except RateLimitExceeded:
        pass


def test_get_remaining():
    rl = RateLimiter()
    rl.set_limit("rem_key", 5, 60)
    assert rl.get_remaining("rem_key") == 5
    rl.check("rem_key")
    assert rl.get_remaining("rem_key") == 4


def test_reset():
    rl = RateLimiter()
    rl.set_limit("reset_key", 2, 60)
    rl.check("reset_key")
    rl.check("reset_key")
    assert rl.check("reset_key") is False
    rl.reset("reset_key")
    assert rl.check("reset_key") is True
