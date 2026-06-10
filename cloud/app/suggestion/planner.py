"""多步信息收集规划器，用于将拜访触发上下文拆解为工具调用计划。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Literal

try:
    from shared.base import AppException, ErrorCode
except ModuleNotFoundError:

    class ErrorCode(IntEnum):
        """依赖缺失时使用的最小错误码回退。"""

        VALIDATION_ERROR = 4

    class AppException(Exception):
        """依赖缺失时使用的最小应用异常回退。"""

        def __init__(self, code: ErrorCode, message: str) -> None:
            """初始化应用异常。

            Args:
                code: 错误码。
                message: 错误信息。

            Returns:
                None。
            """
            super().__init__(message)
            self.code = code
            self.message = message

CollectionMode = Literal["parallel", "sequential"]


@dataclass(slots=True)
class CollectionStep:
    """单个信息收集步骤。

    Attributes:
        step_id: 步骤唯一标识。
        tool_name: 需要调用的工具名称。
        input_args: 工具输入参数。
        expected_result: 期望得到的信息内容。
        depends_on: 前置步骤 ID 列表。
        source: 信息来源名称。
    """

    step_id: str
    tool_name: str
    input_args: dict[str, Any]
    expected_result: str
    depends_on: list[str] = field(default_factory=list)
    source: str = ""


@dataclass(slots=True)
class CollectionPlan:
    """结构化信息收集计划。

    Attributes:
        context: 原始触发上下文。
        mode: 收集模式，支持 parallel 与 sequential。
        steps: 需要执行的步骤列表。
        max_steps: 计划最大步骤数。
    """

    context: dict[str, Any]
    mode: CollectionMode
    steps: list[CollectionStep]
    max_steps: int = 10


class InfoCollectionPlanner:
    """根据代表与 HCP 上下文生成多来源信息收集计划。"""

    def plan(self, context: dict[str, Any]) -> CollectionPlan:
        """生成结构化收集计划。

        Args:
            context: 触发上下文，至少包含 rep_id 与 hcp_id。

        Returns:
            包含工具调用步骤与依赖关系的 CollectionPlan。

        Raises:
            AppException: 缺少必要上下文字段时抛出。
        """
        rep_id = self._required(context, "rep_id")
        hcp_id = self._required(context, "hcp_id")
        mode = self._resolve_mode(context)
        steps = self._build_parallel_steps(rep_id, hcp_id, context)
        if mode == "sequential":
            steps = self._link_sequential_steps(steps)
        return CollectionPlan(context=dict(context), mode=mode, steps=steps)

    def _required(self, context: dict[str, Any], key: str) -> Any:
        """读取必填上下文字段。

        Args:
            context: 触发上下文字典。
            key: 字段名。

        Returns:
            字段值。

        Raises:
            AppException: 字段不存在或为空时抛出。
        """
        value = context.get(key)
        if value in (None, ""):
            raise AppException(ErrorCode.VALIDATION_ERROR, f"Missing required context field: {key}")
        return value

    def _resolve_mode(self, context: dict[str, Any]) -> CollectionMode:
        """解析收集模式。

        Args:
            context: 触发上下文字典。

        Returns:
            合法的收集模式，默认 parallel。

        Raises:
            AppException: 模式值非法时抛出。
        """
        mode = context.get("collection_mode", "parallel")
        if mode not in ("parallel", "sequential"):
            raise AppException(ErrorCode.VALIDATION_ERROR, "collection_mode must be parallel or sequential")
        return mode

    def _build_parallel_steps(self, rep_id: Any, hcp_id: Any, context: dict[str, Any]) -> list[CollectionStep]:
        """创建可并行执行的基础步骤。

        Args:
            rep_id: 代表 ID。
            hcp_id: HCP ID。
            context: 触发上下文。

        Returns:
            基础信息来源步骤列表。
        """
        base_args = {"rep_id": rep_id, "hcp_id": hcp_id}
        market_keywords = context.get("market_keywords") or ["竞品", "适应症", "价格", "学术会议"]
        return [
            CollectionStep(
                step_id="hcp_profile",
                tool_name="query_hcp_profile",
                input_args={"hcp_id": hcp_id},
                expected_result="HCP画像、科室、职称、专长与统一评分",
                source="HCP画像",
            ),
            CollectionStep(
                step_id="visit_history",
                tool_name="query_visit_history",
                input_args={**base_args, "limit": context.get("visit_limit", 5)},
                expected_result="历史拜访频次、内容、最近异议与跟进行动",
                source="历史拜访",
            ),
            CollectionStep(
                step_id="competitor_intel",
                tool_name="query_competitor_intel",
                input_args={**base_args, "window_days": context.get("intel_window_days", 7)},
                expected_result="竞品新品、价格、营销动作与负面事件",
                source="竞品动态",
            ),
            CollectionStep(
                step_id="market_intel",
                tool_name="query_market_intel",
                input_args={"keywords": market_keywords, "limit": context.get("market_limit", 10)},
                expected_result="市场情报、政策信号、学术热点与区域趋势",
                source="市场情报",
            ),
            CollectionStep(
                step_id="causal_attribution",
                tool_name="run_causal_attribution",
                input_args={**base_args, "strategy_id": context.get("strategy_id", "sales_suggestion")},
                expected_result="拜访频率、关系强度、竞品威胁等因素的因果影响",
                depends_on=["visit_history", "competitor_intel"],
                source="因果推断",
            ),
        ]

    def _link_sequential_steps(self, steps: list[CollectionStep]) -> list[CollectionStep]:
        """将基础步骤转换为串行依赖链。

        Args:
            steps: 基础步骤列表。

        Returns:
            带串行依赖的步骤列表。
        """
        linked: list[CollectionStep] = []
        previous_id = ""
        for step in steps:
            depends_on = step.depends_on or ([previous_id] if previous_id else [])
            linked.append(
                CollectionStep(
                    step_id=step.step_id,
                    tool_name=step.tool_name,
                    input_args=step.input_args,
                    expected_result=step.expected_result,
                    depends_on=depends_on,
                    source=step.source,
                )
            )
            previous_id = step.step_id
        return linked
