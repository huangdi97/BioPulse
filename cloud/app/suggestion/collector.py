"""信息来源收集执行器，负责按计划调用服务并整理因果推断结果。"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

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

from .planner import CollectionPlan, CollectionStep

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "cloud.db")


@dataclass(slots=True)
class CollectionResult:
    """信息收集结果。

    Attributes:
        context: 原始触发上下文。
        data: 按步骤 ID 汇总的收集数据。
        completed_steps: 成功完成的步骤 ID。
        failed_steps: 失败步骤与错误信息。
        causal_result: 因果推断输出。
    """

    context: dict[str, Any]
    data: dict[str, Any] = field(default_factory=dict)
    completed_steps: list[str] = field(default_factory=list)
    failed_steps: dict[str, str] = field(default_factory=dict)
    causal_result: dict[str, Any] = field(default_factory=dict)


class InfoCollector:
    """执行信息收集计划并汇总多来源数据。"""

    def __init__(self, db: sqlite3.Connection | None = None) -> None:
        """初始化信息收集器。

        Args:
            db: 可选数据库连接；未提供时使用云端默认 SQLite 数据库。

        Returns:
            None。
        """
        self.db = db or self._connect_default_db()

    def execute(self, plan: CollectionPlan) -> CollectionResult:
        """按计划执行信息收集。

        Args:
            plan: InfoCollectionPlanner 生成的 CollectionPlan。

        Returns:
            包含全部收集数据与失败信息的 CollectionResult。
        """
        result = CollectionResult(context=dict(plan.context))
        for step in self._ordered_steps(plan):
            self._execute_step(step, result)
        result.causal_result = result.data.get("causal_attribution", {})
        return result

    def _connect_default_db(self) -> sqlite3.Connection:
        """创建默认 SQLite 数据库连接。

        Args:
            无。

        Returns:
            配置好 row_factory 的 SQLite 连接。
        """
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        return db

    def _ordered_steps(self, plan: CollectionPlan) -> list[CollectionStep]:
        """根据依赖关系返回执行顺序。

        Args:
            plan: 信息收集计划。

        Returns:
            排序后的步骤列表。
        """
        if plan.mode == "parallel":
            return plan.steps
        remaining = {step.step_id: step for step in plan.steps}
        ordered: list[CollectionStep] = []
        while remaining:
            ready = [step for step in remaining.values() if all(dep in {s.step_id for s in ordered} for dep in step.depends_on)]
            if not ready:
                return plan.steps
            for step in ready:
                ordered.append(step)
                remaining.pop(step.step_id, None)
        return ordered

    def _execute_step(self, step: CollectionStep, result: CollectionResult) -> None:
        """执行单个收集步骤并记录结果。

        Args:
            step: 当前收集步骤。
            result: 正在累积的收集结果。

        Returns:
            None。
        """
        try:
            result.data[step.step_id] = self._dispatch(step)
            result.completed_steps.append(step.step_id)
        except AppException as exc:
            result.failed_steps[step.step_id] = exc.message
        except Exception as exc:
            result.failed_steps[step.step_id] = str(exc)

    def _dispatch(self, step: CollectionStep) -> dict[str, Any]:
        """按工具名分发到对应收集逻辑。

        Args:
            step: 当前收集步骤。

        Returns:
            当前步骤的结构化输出。

        Raises:
            AppException: 工具名不支持时抛出。
        """
        from .collector_hcp import query_hcp_profile
        from .collector_visit import query_visit_history
        from .collector_intel import query_competitor_intel, query_market_intel
        from .collector_causal import run_causal_attribution

        handlers = {
            "query_hcp_profile": lambda args: query_hcp_profile(self.db, args),
            "query_visit_history": lambda args: query_visit_history(self.db, args),
            "query_competitor_intel": lambda args: query_competitor_intel(self.db, args),
            "query_market_intel": lambda args: query_market_intel(self.db, args),
            "run_causal_attribution": lambda args: run_causal_attribution(self.db, args),
        }
        handler = handlers.get(step.tool_name)
        if handler is None:
            raise AppException(ErrorCode.VALIDATION_ERROR, f"Unsupported collection tool: {step.tool_name}")
        return handler(step.input_args)
