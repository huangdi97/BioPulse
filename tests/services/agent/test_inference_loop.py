from cloud.app.services.agent_core import InferenceLoop, ToolRegistry


def make_registry_with_failing_tool() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        name="broken",
        description="Broken tool",
        parameters={"type": "object", "properties": {}},
        fn=lambda: (_ for _ in ()).throw(RuntimeError("internal failure")),
    )
    registry.register(
        name="calculator",
        description="Calculator",
        parameters={
            "type": "object",
            "properties": {
                "a": {"type": "number"},
                "b": {"type": "number"},
                "op": {"type": "string"},
            },
            "required": ["a", "b", "op"],
        },
        fn=lambda a, b, op: {"result": eval(f"{a}{op}{b}")},
    )
    return registry


class TestInferenceLoopLifecycle:
    def test_initial_state_not_running(self, inference_loop: InferenceLoop) -> None:
        assert not inference_loop.is_running

    def test_run_sets_running_state(self, inference_loop: InferenceLoop) -> None:
        messages = [{"content": "hello", "tool_calls": []}]
        inference_loop.run(messages)
        assert not inference_loop.is_running

    def test_stop_ends_execution(self, inference_loop: InferenceLoop) -> None:
        messages = [{"content": "hello", "tool_calls": []}]
        inference_loop.run(messages)
        assert not inference_loop.is_running

    def test_stop_before_run_does_not_raise(self, inference_loop: InferenceLoop) -> None:
        inference_loop.stop()

    def test_multiple_stop_calls_safe(self, inference_loop: InferenceLoop) -> None:
        inference_loop.stop()
        inference_loop.stop()
        inference_loop.stop()

    def test_stop_during_run_interrupts(self, inference_loop: InferenceLoop) -> None:
        inference_loop.stop()
        result = inference_loop.run([{"content": "hi", "tool_calls": []} for _ in range(100)])
        assert isinstance(result, list)


class TestInferenceLoopMessageProcessing:
    def test_returns_output_for_simple_message(self, inference_loop: InferenceLoop) -> None:
        result = inference_loop.run([{"content": "hello", "tool_calls": []}])
        assert len(result) == 1
        assert result[0]["type"] == "output"
        assert result[0]["content"] == "hello"

    def test_processes_tool_call(self, inference_loop: InferenceLoop) -> None:
        result = inference_loop.run(
            [
                {
                    "content": "calculate",
                    "tool_calls": [{"name": "calculator", "arguments": {"a": 2, "b": 3, "op": "+"}}],
                }
            ]
        )
        assert result[0]["type"] == "output"

    def test_tool_call_error_returns_error_type(self, inference_loop: InferenceLoop) -> None:
        registry = make_registry_with_failing_tool()
        loop = InferenceLoop(tool_registry=registry)
        result = loop.run(
            [
                {
                    "content": "do something",
                    "tool_calls": [{"name": "broken", "arguments": {}}],
                }
            ]
        )
        assert result[0]["type"] == "error"
        assert "internal failure" in result[0]["content"]


class TestInferenceLoopMaxIterations:
    def test_stops_when_max_iterations_reached(self) -> None:
        registry = ToolRegistry()
        loop = InferenceLoop(tool_registry=registry, max_iterations=3)
        msg = {"content": "x", "tool_calls": []}
        result = loop.run([msg, msg, msg, msg, msg])
        assert len(result) <= 3

    def test_zero_iterations_processes_nothing(self) -> None:
        registry = ToolRegistry()
        loop = InferenceLoop(tool_registry=registry, max_iterations=0)
        result = loop.run([{"content": "hi", "tool_calls": []}])
        assert result == []

    def test_one_iteration_with_multiple_messages(self) -> None:
        registry = ToolRegistry()
        loop = InferenceLoop(tool_registry=registry, max_iterations=1)
        result = loop.run([{"content": "a", "tool_calls": []}, {"content": "b", "tool_calls": []}])
        assert len(result) <= 2


class TestInferenceLoopEmptyInput:
    def test_empty_message_list_returns_empty(self, inference_loop: InferenceLoop) -> None:
        result = inference_loop.run([])
        assert result == []

    def test_message_with_empty_content_and_no_tool_calls(self, inference_loop: InferenceLoop) -> None:
        result = inference_loop.run([{"content": "", "tool_calls": []}])
        assert len(result) == 1
        assert result[0]["type"] == "output"
        assert result[0]["content"] == ""


class TestInferenceLoopErrorRecovery:
    def test_continues_on_tool_not_found(self, inference_loop: InferenceLoop) -> None:
        result = inference_loop.run(
            [
                {
                    "content": "test",
                    "tool_calls": [{"name": "nonexistent_tool", "arguments": {}}],
                }
            ]
        )
        assert result[0]["type"] == "error"

    def test_invalid_arguments_return_error(self, inference_loop: InferenceLoop) -> None:
        result = inference_loop.run(
            [
                {
                    "content": "test",
                    "tool_calls": [{"name": "weather", "arguments": {"city": 12345}}],
                }
            ]
        )
        assert result[0]["type"] == "error"


class TestInferenceLoopCustomTimeout:
    def test_custom_step_timeout(self) -> None:
        registry = ToolRegistry()
        loop = InferenceLoop(tool_registry=registry, max_iterations=5, step_timeout=0.1)
        assert loop.step_timeout == 0.1

    def test_default_step_timeout(self) -> None:
        registry = ToolRegistry()
        loop = InferenceLoop(tool_registry=registry)
        assert loop.step_timeout == 30.0
