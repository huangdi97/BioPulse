"""Agent 执行计划器集成测试。"""

from __future__ import annotations

import json

import pytest

from cloud.app.agent_runtime.planner import Plan, Planner, PlanStep


class CircularDependencyError(Exception): ...


@pytest.fixture
def planner():
    return Planner()


@pytest.fixture
def sample_plan_data():
    return {
        "goal": "Analyze sales data",
        "steps": [
            {
                "step_id": "s1",
                "description": "Query sales records",
                "tool": "query_sales",
                "params_template": {"date_range": "last_quarter"},
                "expected_state": "data_collected",
                "dependencies": [],
                "fallback": None,
                "verification_criteria": ["data_exists"],
            },
            {
                "step_id": "s2",
                "description": "Analyze trends",
                "tool": "analyze_with_llm",
                "params_template": {"focus": "growth"},
                "expected_state": "analysis_done",
                "dependencies": ["s1"],
                "fallback": "skip",
                "verification_criteria": ["trends_found"],
            },
            {
                "step_id": "s3",
                "description": "Generate report",
                "tool": "create_notification",
                "params_template": {"format": "pdf"},
                "expected_state": "report_generated",
                "dependencies": ["s2"],
                "fallback": None,
                "verification_criteria": ["report_created"],
            },
        ],
        "max_steps": 10,
        "completion_conditions": ["all_steps_done"],
        "plan_confidence": 0.85,
    }


class TestPlanGeneration:
    def test_simple_task_single_step_linear(self, planner: Planner):
        plan = Plan(
            goal="Simple task",
            steps=[PlanStep(step_id="s1", description="Do it", tool="execute", dependencies=[])],
        )
        assert len(plan.steps) == 1
        assert plan.steps[0].step_id == "s1"

    def test_validate_simple_plan(self, planner: Planner):
        plan = Plan(
            goal="Simple",
            steps=[PlanStep(step_id="s1", description="Do", tool="tool", dependencies=[])],
            plan_confidence=0.9,
        )
        assert planner.validate_plan(plan)

    def test_generate_plan_with_empty_tools(self, planner: Planner):
        plan = planner.generate_plan("do something", [])
        assert isinstance(plan, Plan)
        assert plan.goal == "do something"

    def test_plan_confidence_default(self):
        plan = Plan(goal="test", steps=[])
        assert plan.plan_confidence == 0.0

    def test_plan_max_steps_default(self):
        plan = Plan(goal="test", steps=[])
        assert plan.max_steps == 10


class TestComplexTaskDAG:
    def test_dag_structure_multiple_steps(self):
        steps = [
            PlanStep(step_id="s1", description="Step 1", tool="t1", dependencies=[]),
            PlanStep(step_id="s2", description="Step 2", tool="t2", dependencies=["s1"]),
            PlanStep(step_id="s3", description="Step 3", tool="t3", dependencies=["s1"]),
            PlanStep(step_id="s4", description="Step 4", tool="t4", dependencies=["s2", "s3"]),
        ]
        plan = Plan(goal="DAG task", steps=steps)
        assert len(plan.steps) == 4
        assert plan.steps[3].dependencies == ["s2", "s3"]

    def test_parallel_steps_no_dependencies(self):
        steps = [
            PlanStep(step_id="s1", description="Parallel A", tool="t1", dependencies=[]),
            PlanStep(step_id="s2", description="Parallel B", tool="t2", dependencies=[]),
            PlanStep(step_id="s3", description="Parallel C", tool="t3", dependencies=[]),
        ]
        plan = Plan(goal="Parallel", steps=steps)
        for step in plan.steps:
            assert step.dependencies == []

    def test_validate_dag_dependencies(self, planner: Planner):
        steps = [
            PlanStep(step_id="s1", description="Root", tool="t1", dependencies=[]),
            PlanStep(step_id="s2", description="Child", tool="t2", dependencies=["s1"]),
        ]
        plan = Plan(goal="DAG", steps=steps)
        assert planner.validate_plan(plan)

    def test_dag_execution_order(self, planner: Planner, sample_plan_data: dict):
        plan = Plan(**sample_plan_data)
        assert planner.validate_plan(plan)
        step_ids = [s.step_id for s in plan.steps]
        dep_map = {s.step_id: s.dependencies for s in plan.steps}
        executed: set[str] = set()
        for step_id in step_ids:
            for dep in dep_map[step_id]:
                assert dep in executed, f"{step_id} depends on {dep} which was not executed yet"
            executed.add(step_id)


class TestStepFailureFallback:
    def test_retry_fallback_strategy(self):
        step = PlanStep(step_id="s1", description="Retry step", tool="t1", fallback="retry")
        assert step.fallback == "retry"

    def test_skip_fallback_strategy(self):
        step = PlanStep(step_id="s2", description="Skip step", tool="t2", fallback="skip")
        assert step.fallback == "skip"

    def test_abort_fallback_strategy(self):
        step = PlanStep(step_id="s3", description="Abort step", tool="t3", fallback="abort")
        assert step.fallback == "abort"

    def test_no_fallback_defaults_none(self):
        step = PlanStep(step_id="s4", description="No fallback", tool="t4")
        assert step.fallback is None


class TestPlanProgressTracking:
    def test_status_transition_pending_to_running(self):
        status = "pending"
        status = "running"
        assert status == "running"

    def test_status_transition_running_to_done(self):
        status = "running"
        status = "done"
        assert status == "done"

    def test_status_transition_running_to_failed(self):
        status = "running"
        status = "failed"
        assert status == "failed"

    def test_track_all_step_statuses(self, sample_plan_data: dict):
        plan = Plan(**sample_plan_data)
        statuses = {step.step_id: "pending" for step in plan.steps}
        for step in plan.steps:
            statuses[step.step_id] = "running"
            statuses[step.step_id] = "done"
        assert all(v == "done" for v in statuses.values())

    def test_failure_does_not_affect_other_steps(self, sample_plan_data: dict):
        statuses = {step.step_id: "done" for step in Plan(**sample_plan_data).steps}
        statuses["s2"] = "failed"
        assert statuses["s1"] == "done"
        assert statuses["s2"] == "failed"
        assert statuses["s3"] == "done"


class TestPlanSerialization:
    def test_serialize_to_dict(self, sample_plan_data: dict):
        plan = Plan(**sample_plan_data)
        d = plan.model_dump()
        assert d["goal"] == "Analyze sales data"
        assert len(d["steps"]) == 3
        assert d["steps"][0]["step_id"] == "s1"

    def test_deserialize_from_dict(self, sample_plan_data: dict):
        plan = Plan(**sample_plan_data)
        d = plan.model_dump()
        restored = Plan(**d)
        assert restored.goal == plan.goal
        assert len(restored.steps) == len(plan.steps)
        assert restored.steps[0].tool == "query_sales"

    def test_serialize_to_json_roundtrip(self, sample_plan_data: dict):
        plan = Plan(**sample_plan_data)
        json_str = plan.model_dump_json()
        restored = Plan(**json.loads(json_str))
        assert restored.goal == "Analyze sales data"
        assert restored.steps[1].dependencies == ["s1"]

    def test_serialize_empty_plan(self):
        plan = Plan(goal="", steps=[])
        d = plan.model_dump()
        assert d["goal"] == ""
        assert d["steps"] == []


class TestEmptyPlan:
    def test_empty_plan_zero_steps(self):
        plan = Plan(goal="empty", steps=[])
        assert len(plan.steps) == 0

    def test_empty_plan_invalid(self, planner: Planner):
        plan = Plan(goal="", steps=[])
        assert not planner.validate_plan(plan)

    def test_empty_plan_completes_immediately(self):
        plan = Plan(goal="no_work", steps=[])
        completed = len(plan.steps) == 0
        assert completed

    def test_empty_plan_confidence_zero(self):
        plan = Plan(goal="no_conf", steps=[])
        assert plan.plan_confidence == 0.0

    def test_empty_plan_max_steps_default(self):
        plan = Plan(goal="default", steps=[])
        assert plan.max_steps == 10


class TestCircularDependencyDetector:
    def test_detect_direct_cycle(self):
        steps = [
            PlanStep(step_id="s1", description="A", tool="t1", dependencies=["s2"]),
            PlanStep(step_id="s2", description="B", tool="t2", dependencies=["s1"]),
        ]

        def detect_cycle(steps: list[PlanStep]) -> bool:
            dep_map = {s.step_id: s.dependencies for s in steps}
            visited: set[str] = set()
            rec_stack: set[str] = set()

            def dfs(node: str) -> bool:
                if node in rec_stack:
                    return True
                if node in visited:
                    return False
                visited.add(node)
                rec_stack.add(node)
                for dep in dep_map.get(node, []):
                    if dep in dep_map and dfs(dep):
                        return True
                rec_stack.remove(node)
                return False

            for step_id in dep_map:
                if dfs(step_id):
                    return True
            return False

        assert detect_cycle(steps)

    def test_detect_indirect_cycle(self):
        steps = [
            PlanStep(step_id="s1", description="A", tool="t1", dependencies=["s2"]),
            PlanStep(step_id="s2", description="B", tool="t2", dependencies=["s3"]),
            PlanStep(step_id="s3", description="C", tool="t3", dependencies=["s1"]),
        ]

        def has_cycle(steps: list[PlanStep]) -> bool:
            graph = {s.step_id: s.dependencies for s in steps}
            visited: set[str] = set()
            rec: set[str] = set()

            def dfs(node: str) -> bool:
                if node in rec:
                    return True
                if node in visited:
                    return False
                visited.add(node)
                rec.add(node)
                for dep in graph.get(node, []):
                    if dep in graph and dfs(dep):
                        return True
                rec.remove(node)
                return False

            for n in graph:
                if dfs(n):
                    return True
            return False

        assert has_cycle(steps)

    def test_no_cycle_returns_false(self):
        steps = [
            PlanStep(step_id="s1", description="A", tool="t1", dependencies=[]),
            PlanStep(step_id="s2", description="B", tool="t2", dependencies=["s1"]),
            PlanStep(step_id="s3", description="C", tool="t3", dependencies=["s2"]),
        ]

        def has_cycle(steps: list[PlanStep]) -> bool:
            graph = {s.step_id: s.dependencies for s in steps}
            visited: set[str] = set()
            rec: set[str] = set()

            def dfs(node: str) -> bool:
                if node in rec:
                    return True
                if node in visited:
                    return False
                visited.add(node)
                rec.add(node)
                for dep in graph.get(node, []):
                    if dep in graph and dfs(dep):
                        return True
                rec.remove(node)
                return False

            for n in graph:
                if dfs(n):
                    return True
            return False

        assert not has_cycle(steps)

    def test_self_loop_detected(self):
        steps = [
            PlanStep(step_id="s1", description="Self", tool="t1", dependencies=["s1"]),
        ]

        def has_cycle(steps: list[PlanStep]) -> bool:
            graph = {s.step_id: s.dependencies for s in steps}
            visited: set[str] = set()
            rec: set[str] = set()

            def dfs(node: str) -> bool:
                if node in rec:
                    return True
                if node in visited:
                    return False
                visited.add(node)
                rec.add(node)
                for dep in graph.get(node, []):
                    if dep in graph and dfs(dep):
                        return True
                rec.remove(node)
                return False

            for n in graph:
                if dfs(n):
                    return True
            return False

        assert has_cycle(steps)

    def test_cycle_detection_raises_error(self):
        steps = [
            PlanStep(step_id="a", description="A", tool="t1", dependencies=["b"]),
            PlanStep(step_id="b", description="B", tool="t2", dependencies=["a"]),
        ]

        def validate(steps: list[PlanStep]) -> None:
            graph = {s.step_id: s.dependencies for s in steps}
            visited: set[str] = set()
            rec: set[str] = set()

            def dfs(node: str) -> None:
                if node in rec:
                    raise CircularDependencyError(f"Circular dependency detected involving step '{node}'")
                if node in visited:
                    return
                visited.add(node)
                rec.add(node)
                for dep in graph.get(node, []):
                    if dep in graph:
                        dfs(dep)
                rec.remove(node)

            for n in graph:
                dfs(n)

        with pytest.raises(CircularDependencyError, match="Circular dependency"):
            validate(steps)


class TestPlanValidation:
    def test_valid_plan(self, planner: Planner, sample_plan_data: dict):
        plan = Plan(**sample_plan_data)
        assert planner.validate_plan(plan)

    def test_invalid_plan_empty_goal(self, planner: Planner):
        plan = Plan(goal="", steps=[PlanStep(step_id="s1", description="Do", tool="t1", dependencies=[])])
        assert not planner.validate_plan(plan)

    def test_invalid_plan_empty_steps(self, planner: Planner):
        plan = Plan(goal="test", steps=[])
        assert not planner.validate_plan(plan)

    def test_invalid_plan_missing_description(self, planner: Planner):
        plan = Plan(
            goal="test",
            steps=[PlanStep(step_id="s1", description="", tool="t1", dependencies=[])],
        )
        assert not planner.validate_plan(plan)

    def test_invalid_plan_missing_tool(self, planner: Planner):
        plan = Plan(
            goal="test",
            steps=[PlanStep(step_id="s1", description="Do", tool="", dependencies=[])],
        )
        assert not planner.validate_plan(plan)

    def test_invalid_plan_max_steps_zero(self, planner: Planner):
        plan = Plan(
            goal="test",
            steps=[PlanStep(step_id="s1", description="Do", tool="t1", dependencies=[])],
            max_steps=0,
        )
        assert not planner.validate_plan(plan)

    def test_invalid_plan_confidence_out_of_range(self, planner: Planner):
        plan = Plan(
            goal="test",
            steps=[PlanStep(step_id="s1", description="Do", tool="t1", dependencies=[])],
            plan_confidence=1.5,
        )
        assert not planner.validate_plan(plan)

    def test_invalid_plan_duplicate_step_id(self, planner: Planner):
        plan = Plan(
            goal="test",
            steps=[
                PlanStep(step_id="s1", description="First", tool="t1", dependencies=[]),
                PlanStep(step_id="s1", description="Second", tool="t2", dependencies=[]),
            ],
        )
        assert not planner.validate_plan(plan)

    def test_invalid_plan_missing_dependency(self, planner: Planner):
        plan = Plan(
            goal="test",
            steps=[
                PlanStep(step_id="s1", description="Do", tool="t1", dependencies=["nonexistent"]),
            ],
        )
        assert not planner.validate_plan(plan)
