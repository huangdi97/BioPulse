from cloud.app.agent_runtime.models import AgentDecision


class LoopDetector:
    """检测 Agent 决策历史中的循环模式，提供降级建议。

    支持的检测模式：
    - 严格重复模式 (strict repeat): 同一工具 + 相同参数被连续调用 N 次
    - 交替模式 (alternating pattern): A→B→A→B→A 两个工具互相交替调用

    可配置阈值：
        max_loop_count: 触发严格重复检测的连续相同调用次数，默认 3
        max_pattern_length: 触发交替模式检测的序列长度，默认 5

    保护机制：
        检测到循环时自动生成降级策略建议，包括：
        - 降低 max_iterations 限制循环次数
        - 提高 temperature 增加随机性
        - 添加显式停止条件
        - 针对具体模式重写工具或合并工具
    """

    def __init__(self, max_loop_count: int = 3, max_pattern_length: int = 5) -> None:
        """初始化循环检测器。

        Args:
            max_loop_count: 同一工具相同参数连续调用多少次即判定为严格重复循环。
            max_pattern_length: 交替模式检测的最小序列长度（建议为奇数，如 5、7）。
        """
        self.max_loop_count = max_loop_count
        self.max_pattern_length = max_pattern_length
        self.history: list[AgentDecision] = []

    def record(self, decision: AgentDecision) -> None:
        """记录一次 Agent 决策到历史中。

        Args:
            decision: Agent 的一次决策（包含 action、tool、params 等字段）。
        """
        self.history.append(decision)

    def detect(self) -> str | None:
        """检测历史中是否存在循环模式。

        Returns:
            如果检测到循环，返回包含模式描述和降级建议的字符串；
            如果未检测到循环，返回 None。
        """
        result = self._detect_strict_repeat()
        if result:
            return result
        return self._detect_alternating_pattern()

    def _detect_strict_repeat(self) -> str | None:
        """检测最近 N 次调用是否为同一工具 + 相同参数。"""
        if self.max_loop_count < 2 or len(self.history) < self.max_loop_count:
            return None
        recent = self.history[-self.max_loop_count :]
        names = [d.tool for d in recent]
        params = [str(d.params) for d in recent]
        if len(set(names)) == 1 and all(p == params[0] for p in params):
            tool_name = names[0]
            return self._build_message("strict_repeat", tool_name)
        return None

    def _detect_alternating_pattern(self) -> str | None:
        """检测历史末尾是否存在 A→B→A→B→A 交替模式。"""
        if self.max_pattern_length < 3 or len(self.history) < self.max_pattern_length:
            return None
        recent = self.history[-self.max_pattern_length :]
        names = [d.tool for d in recent]
        if len(set(names)) != 2:
            return None
        a, b = names[0], names[1]
        if a == b:
            return None
        expected = [a if i % 2 == 0 else b for i in range(self.max_pattern_length)]
        if names == expected:
            return self._build_message("alternating_pattern", f"{a}/{b}")
        return None

    def _build_message(self, pattern_type: str, tool_label: str) -> str:
        """构建包含描述和降级建议的检测消息。"""
        if pattern_type == "strict_repeat":
            desc = f"Loop detected (strict repeat): tool '{tool_label}' called {self.max_loop_count} times with identical params"
        else:
            desc = f"Loop detected (alternating pattern): tools '{tool_label}' oscillating {self.max_pattern_length} times"
        suggestions = self._suggest_downgrade(tool_label, pattern_type)
        return desc + "\n" + "\n".join(suggestions)

    def _suggest_downgrade(self, tool_label: str, pattern_type: str) -> list[str]:
        """根据检测到的循环模式生成降级策略建议。"""
        suggestions = [
            "  [1] Downgrade: reduce max_iterations to limit the loop",
            "  [2] Downgrade: increase temperature to introduce randomness",
            "  [3] Downgrade: add explicit stop condition after {} similar calls".format(
                self.max_loop_count if pattern_type == "strict_repeat" else self.max_pattern_length
            ),
        ]
        if pattern_type == "strict_repeat":
            suggestions.append(f"  [4] Downgrade: rewrite tool '{tool_label}' to return a termination signal on repeated input")
        else:
            suggestions.append(f"  [4] Downgrade: merge tools '{tool_label}' or add a coordinator tool to break the oscillation")
        return suggestions

    def reset(self) -> None:
        """清空决策历史，重置检测器状态。"""
        self.history.clear()
