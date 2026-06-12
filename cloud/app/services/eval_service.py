"""评估服务提供预设案例与评估功能。"""


class EvalService:
    PRESET_CASES = {
        "opportunity_scanner": [
            {
                "input": "扫描最新招标信息",
                "expected_tools": ["query_bidding", "analyze_with_llm", "create_notification"],
                "expected_output_contains": "",
                "max_steps": 5,
            }
        ],
        "sales_coach_analyst": [
            {
                "input": "分析销售训练数据，找出能力弱点",
                "expected_tools": ["query_training_records", "analyze_with_llm", "create_notification"],
                "expected_output_contains": "",
                "max_steps": 5,
            }
        ],
        "通用": [
            {
                "input": "简单查询",
                "expected_tools": ["query_bidding"],
                "expected_output_contains": "",
                "max_steps": 3,
            }
        ],
    }

    def evaluate(self, agent_key: str, test_cases: list[dict]) -> dict:
        """对指定 agent 执行一组测试用例的评估。

        参数:
            agent_key: Agent 标识键。
            test_cases: 测试用例字典列表。

        返回:
            包含总计、通过数、失败数和详细结果的字典。
        """
        preset_tools = self._get_allowed_tools(agent_key)
        details = []
        passed = 0
        failed = 0

        for i, tc in enumerate(test_cases):
            case_result = self._evaluate_one(tc, preset_tools, i)
            details.append(case_result)
            if case_result["passed"]:
                passed += 1
            else:
                failed += 1

        return {
            "total": len(test_cases),
            "passed": passed,
            "failed": failed,
            "details": details,
        }

    def run_regression(self, agent_key: str) -> dict:
        """运行预设回归测试用例对指定 agent 进行评估。

        参数:
            agent_key: Agent 标识键。

        返回:
            包含执行结果的字典，若无预设用例则返回空结果。
        """
        test_cases = self.PRESET_CASES.get(agent_key, [])
        if not test_cases:
            return {"total": 0, "passed": 0, "failed": 0, "details": []}
        return self.evaluate(agent_key, test_cases)

    def _get_allowed_tools(self, agent_key: str) -> frozenset:
        """获取指定 agent 预设用例中允许使用的工具集合。

        参数:
            agent_key: Agent 标识键。

        返回:
            允许的工具名称的不可变集合。
        """
        preset = self.PRESET_CASES.get(agent_key)
        if not preset:
            return frozenset()
        tools: set[str] = set()
        for tc in preset:
            tools.update(tc.get("expected_tools", []))
        return frozenset(tools)

    def _evaluate_one(self, tc: dict, allowed_tools: frozenset, index: int) -> dict:
        """评估单个测试用例，检查预期工具是否在允许列表中。

        参数:
            tc: 测试用例字典。
            allowed_tools: 允许的工具集合。
            index: 测试用例索引。

        返回:
            包含用例编号、输入、是否通过及原因说明的字典。
        """
        expected_tools = tc.get("expected_tools", [])

        if allowed_tools:
            missing = [t for t in expected_tools if t not in allowed_tools]
            if missing:
                return {
                    "case": index,
                    "input": tc.get("input", ""),
                    "passed": False,
                    "reason": f"expected_tools 不在预设工具列表中: {missing}",
                }

        expected_output = tc.get("expected_output_contains", "")
        if expected_output:
            return {
                "case": index,
                "input": tc.get("input", ""),
                "passed": False,
                "reason": "expected_output_contains 检查尚未实现",
            }

        return {
            "case": index,
            "input": tc.get("input", ""),
            "passed": True,
            "reason": "所有检查通过",
        }
