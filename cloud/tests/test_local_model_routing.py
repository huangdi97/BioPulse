"""本地模型 routing 端到端测试。

覆盖三种 mode（cloud/local/hybrid）、auto-disable、OpenAI 兼容格式。
不依赖真实 llama.cpp 实例，所有 HTTP 请求通过 mock 隔离。
"""

from unittest.mock import MagicMock, patch

import pytest

from cloud.app.agent_runtime.runtime_llm.core import RuntimeLLM


@pytest.fixture
def mock_core():
    """创建 mock RuntimeCore 实例。"""
    core = MagicMock()
    core._trace_id = "test-trace"
    core._trace_data = []
    core._rate_limiter = None
    core._circuit_breaker = None
    core._tracer = None
    return core


@pytest.fixture
def llm(mock_core):
    """创建 RuntimeLLM 实例（无 circuit breaker，无 rate limiter）。"""
    return RuntimeLLM(core=mock_core)


class TestRoutingModeCloud:
    """mode=cloud 时所有请求走 API。"""

    def test_routes_to_cloud_normal(self, llm):
        """cloud 模式应走 _call_cloud_normal，返回 tier=cloud_normal。"""
        with (
            patch.object(llm, "_call_cloud_normal", return_value={"success": True, "data": {}, "attempts": 1}) as mock_cloud,
            patch(
                "cloud.app.agent_runtime.runtime_llm.core.config_settings.ai_routing_mode",
                "cloud",
            ),
        ):
            result = llm._route_call([{"role": "user", "content": "hello"}], 0.7)
            mock_cloud.assert_called_once()
            assert result.get("model_tier") == "cloud_normal"

    def test_never_calls_local_when_cloud(self, llm):
        """cloud 模式下不应调用 _call_local。"""
        with (
            patch.object(llm, "_call_cloud_normal", return_value={"success": True, "data": {}, "attempts": 1}),
            patch(
                "cloud.app.agent_runtime.runtime_llm.core.config_settings.ai_routing_mode",
                "cloud",
            ),
            patch.object(llm, "_call_local") as mock_local,
        ):
            llm._route_call([{"role": "user", "content": "hi"}], 0.7)
            mock_local.assert_not_called()


class TestRoutingModeLocal:
    """mode=local 时所有请求走本地模型。"""

    def test_routes_to_local(self, llm):
        """local 模式应走 _call_local，返回 tier=local。"""
        with (
            patch.object(llm, "_do_call_local", return_value={"success": True, "data": {}, "attempts": 1}) as mock_local,
            patch(
                "cloud.app.agent_runtime.runtime_llm.core.config_settings.ai_routing_mode",
                "local",
            ),
            patch.object(llm, "_call_cloud_normal") as mock_cloud,
        ):
            llm._route_call([{"role": "user", "content": "hello"}], 0.7)
            mock_local.assert_called_once()
            mock_cloud.assert_not_called()

    def test_local_disabled_fallsback(self, llm):
        """local 模式但模型被 auto-disable 时应走 cloud。"""
        llm._local_disabled = True
        with (
            patch(
                "cloud.app.agent_runtime.runtime_llm.request.call_local",
                return_value={"success": True, "data": {}, "attempts": 1},
            ) as mock_call_local,
            patch(
                "cloud.app.agent_runtime.runtime_llm.core.config_settings.ai_routing_mode",
                "local",
            ),
        ):
            llm._route_call([{"role": "user", "content": "hello"}], 0.7)
            # When disabled, _do_call_local should return cloud result WITHOUT calling call_local
            mock_call_local.assert_not_called()


class TestRoutingModeHybrid:
    """mode=hybrid 时按复杂度路由。"""

    @patch("cloud.app.agent_runtime.runtime_llm.core.config_settings.ai_routing_mode", "hybrid")
    def test_simple_goes_local(self, llm):
        """复杂度≤2 应走 local。"""
        with (
            patch.object(llm, "_estimate_complexity", return_value=1),
            patch.object(llm, "_do_call_local", return_value={"success": True, "data": {}, "attempts": 1}) as mock_local,
            patch.object(llm, "_call_cloud_normal") as mock_cloud,
        ):
            llm._route_call([{"role": "user", "content": "x"}], 0.7)
            mock_local.assert_called_once()
            mock_cloud.assert_not_called()

    @patch("cloud.app.agent_runtime.runtime_llm.core.config_settings.ai_routing_mode", "hybrid")
    def test_medium_goes_cloud(self, llm):
        """复杂度=3 应走 cloud_normal。"""
        with (
            patch.object(llm, "_estimate_complexity", return_value=3),
            patch.object(llm, "_call_cloud_normal", return_value={"success": True, "data": {}, "attempts": 1}) as mock_cloud,
            patch.object(llm, "_call_local") as mock_local,
            patch.object(llm, "_call_cloud_agent") as mock_agent,
        ):
            llm._route_call([{"role": "user", "content": "x" * 1000}], 0.7)
            mock_local.assert_not_called()
            mock_cloud.assert_called_once()
            mock_agent.assert_not_called()

    @patch("cloud.app.agent_runtime.runtime_llm.core.config_settings.ai_routing_mode", "hybrid")
    def test_complex_goes_agent(self, llm):
        """复杂度≥4 应走 cloud_agent。"""
        with (
            patch.object(llm, "_estimate_complexity", return_value=5),
            patch.object(llm, "_call_cloud_agent", return_value={"success": True, "data": {}, "attempts": 1}) as mock_agent,
            patch.object(llm, "_call_local") as mock_local,
            patch.object(llm, "_call_cloud_normal") as mock_cloud,
        ):
            llm._route_call([{"role": "user", "content": "x" * 5000}], 0.7)
            mock_local.assert_not_called()
            mock_cloud.assert_not_called()
            mock_agent.assert_called_once()


class TestLocalAutoDisable:
    """本地模型连续失败3次后自动禁用。"""

    def test_tracks_consecutive_failures(self, llm):
        """连续失败应递增计数器。"""
        with (
            patch.object(llm, "_call_cloud_normal", return_value={"success": True, "data": {}, "attempts": 1}),
            patch("cloud.app.agent_runtime.runtime_llm.core.config_settings.ai_routing_mode", "hybrid"),
            patch.object(llm, "_estimate_complexity", return_value=1),
        ):
            # Mock _do_call_local to return failure 3 times

            def failing_local(messages, temperature, is_async):
                result = {"success": False, "error": "mock failure", "attempts": 1}
                llm._check_local_failures(result)
                return llm._call_cloud_normal(messages, temperature)

            llm._do_call_local = failing_local

            # Call 3 times
            for i in range(3):
                llm._route_call([{"role": "user", "content": "x"}], 0.7)

            assert llm._local_consecutive_failures == 3
            assert llm._local_disabled is True

    def test_resets_on_success(self, llm):
        """成功后应重置计数器。"""
        llm._local_consecutive_failures = 2
        llm._check_local_failures({"success": True, "data": {}, "attempts": 1})
        assert llm._local_consecutive_failures == 0
        assert llm._local_disabled is False


class TestCallLocalOpenAIFormat:
    """call_local 使用 OpenAI 兼容格式。"""

    @patch("cloud.app.agent_runtime.runtime_llm.request.httpx.Client")
    def test_sends_messages_array(self, mock_httpx):
        """请求体应包含 messages 数组而非 prompt。"""
        from cloud.app.agent_runtime.runtime_llm.request import call_local

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello!"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }
        mock_httpx.return_value.__enter__.return_value.post.return_value = mock_response

        config = MagicMock()
        config.ai_local_endpoint = "http://localhost:8080"
        config.ai_local_model = "qwen2.5"

        call_local(
            config,
            [{"role": "user", "content": "hi"}],
            0.7,
            fallback_fn=lambda: {"success": True, "data": {}, "attempts": 1, "model_tier": "cloud_normal"},
        )

        # Verify the request body is OpenAI-compatible
        call_kwargs = mock_httpx.return_value.__enter__.return_value.post.call_args[1]
        body = call_kwargs["json"]
        assert "messages" in body, "Should use messages array (OpenAI format)"
        assert "prompt" not in body, "Should NOT use prompt field (Ollama format)"
        assert body["model"] == "qwen2.5"
        assert body["messages"] == [{"role": "user", "content": "hi"}]

    @patch("cloud.app.agent_runtime.runtime_llm.request.httpx.Client")
    def test_uses_v1_chat_completions_endpoint(self, mock_httpx):
        """URL 应包含 /v1/chat/completions。"""
        from cloud.app.agent_runtime.runtime_llm.request import call_local

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello!"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }
        mock_httpx.return_value.__enter__.return_value.post.return_value = mock_response

        config = MagicMock()
        config.ai_local_endpoint = "http://localhost:8080"
        config.ai_local_model = "qwen2.5"

        call_local(config, [{"role": "user", "content": "hi"}], 0.7, fallback_fn=lambda: {"success": True, "data": {}, "attempts": 1})

        call_url = mock_httpx.return_value.__enter__.return_value.post.call_args[0][0]
        assert "/v1/chat/completions" in call_url

    def test_parses_llamacpp_response(self):
        """应正确处理 llama.cpp 的返回格式。"""
        from cloud.app.agent_runtime.runtime_llm.request import call_local

        with patch("cloud.app.agent_runtime.runtime_llm.request.httpx.Client") as mock_httpx:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Test reply"}}],
                "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
            }
            mock_httpx.return_value.__enter__.return_value.post.return_value = mock_response

            config = MagicMock()
            config.ai_local_endpoint = "http://localhost:8080"
            config.ai_local_model = "test-model"

            result = call_local(
                config,
                [{"role": "user", "content": "test"}],
                0.7,
                fallback_fn=lambda: {"success": True, "data": {}, "attempts": 1},
            )

            assert result["success"] is True
            assert result["data"]["data"]["reply"] == "Test reply"
            assert result["data"]["data"]["usage"]["total_tokens"] == 70
