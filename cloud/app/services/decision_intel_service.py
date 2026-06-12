"""决策情报服务，负责决策案例的创建与AI辅助分析。"""

import json
import urllib.error
import urllib.request
from typing import Any, Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.services.decision_logger import DecisionLogger
from cloud.app.services.intel_analyzer import IntelAnalyzer
from shared.ai_gateway import LLM_INFERENCE_TIMEOUT
from shared.base_service import BaseService
from shared.config import settings as config_settings


def _parse_json(raw: str, default: Any = None) -> Any:
    """安全解析 JSON 字符串。

    Args:
        raw: JSON 字符串
        default: 解析失败时的默认值

    Returns:
        解析后的 Python 对象或默认值
    """
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else raw


def _call_ai(messages: list[dict], auth_header: str) -> dict:
    """调用 AI 推理接口。

    Args:
        messages: 消息列表
        auth_header: 认证头部信息

    Returns:
        AI 返回的数据字典
    """
    payload = {"messages": messages, "temperature": 0.7, "max_tokens": 2048}
    req = urllib.request.Request(
        f"{config_settings.ai_chat_url}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": auth_header},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=LLM_INFERENCE_TIMEOUT) as rp:
        return json.loads(rp.read().decode("utf-8")).get("data", {})


def _e404(name: str = "Resource"):
    """快速抛出 404 异常。

    Args:
        name: 资源名称

    Raises:
        HTTPException: 始终抛出404异常
    """
    raise HTTPException(status.HTTP_404_NOT_FOUND, f"{name} not found")


class DecisionIntelService(BaseService):
    """决策情报服务，提供案例管理与AI辅助因果分析。"""

    def __init__(self, db=None):
        """初始化决策情报服务。

        Args:
            db: 数据库连接对象（可选）
        """
        super().__init__(db)
        self._logger = DecisionLogger(db)
        self._analyzer = IntelAnalyzer(db)

    def create_case(
        self,
        name: str,
        pipeline_run_id: Optional[int],
        description: str,
        outcome: str,
        outcome_score: float,
        context: dict,
        tags: list,
        uid: int,
    ) -> dict:
        """创建决策案例。

        Args:
            name: 案例名称
            pipeline_run_id: 流水线运行ID（可选）
            description: 案例描述
            outcome: 结果描述
            outcome_score: 结果评分
            context: 上下文信息
            tags: 标签列表
            uid: 创建者用户ID

        Returns:
            创建的案例字典
        """
        return self._logger.create_case(name, pipeline_run_id, description, outcome, outcome_score, context, tags, uid)

    def list_cases(
        self,
        outcome_score_min: Optional[float] = None,
        outcome_score_max: Optional[float] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """查询决策案例列表，支持评分范围、标签、关键词筛选和分页。

        Args:
            outcome_score_min: 最低结果评分（可选）
            outcome_score_max: 最高结果评分（可选）
            tag: 标签筛选（可选）
            search: 关键词搜索（可选）
            page: 页码
            page_size: 每页数量

        Returns:
            案例列表和分页信息
        """
        return self._logger.list_cases(outcome_score_min, outcome_score_max, tag, search, page, page_size)

    def get_case(self, case_id: int) -> dict:
        """获取案例详情。

        Args:
            case_id: 案例ID

        Returns:
            案例详情字典
        """
        return self._logger.get_case(case_id)

    def update_case(
        self,
        case_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        outcome: Optional[str] = None,
        outcome_score: Optional[float] = None,
        context: Optional[dict] = None,
        tags: Optional[list] = None,
    ) -> dict:
        """更新决策案例。

        Args:
            case_id: 案例ID
            name: 新名称（可选）
            description: 新描述（可选）
            outcome: 新结果描述（可选）
            outcome_score: 新结果评分（可选）
            context: 新上下文信息（可选）
            tags: 新标签列表（可选）

        Returns:
            更新后的案例字典
        """
        return self._logger.update_case(case_id, name, description, outcome, outcome_score, context, tags)

    def delete_case(self, case_id: int) -> None:
        """删除决策案例。

        Args:
            case_id: 案例ID
        """
        return self._logger.delete_case(case_id)

    def analyze_case(self, case_id: int, custom_question: str, auth_header: str) -> dict:
        """对决策案例进行AI辅助分析。

        Args:
            case_id: 案例ID
            custom_question: 自定义问题
            auth_header: 认证头部信息

        Returns:
            分析结果字典
        """
        return self._analyzer.analyze_case(case_id, custom_question, auth_header)

    def list_analyses(self, case_id: int) -> list:
        """查询案例的所有分析记录。

        Args:
            case_id: 案例ID

        Returns:
            分析记录列表
        """
        return self._analyzer.list_analyses(case_id)

    def get_analysis(self, analysis_id: int) -> dict:
        """获取单条分析记录详情。

        Args:
            analysis_id: 分析记录ID

        Returns:
            分析记录详情字典
        """
        return self._analyzer.get_analysis(analysis_id)

    def reflect(self, filter_tags: list, max_cases: int, auth_header: str) -> dict:
        """跨案例反思分析，总结模式与洞察。

        Args:
            filter_tags: 筛选标签列表
            max_cases: 最大案例数
            auth_header: 认证头部信息

        Returns:
            反思分析结果字典
        """
        return self._analyzer.reflect(filter_tags, max_cases, auth_header)

    def list_insights(
        self,
        insight_type: Optional[str] = None,
        confidence_min: Optional[float] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """查询洞察列表，支持按类型、置信度筛选和分页。

        Args:
            insight_type: 洞察类型（可选）
            confidence_min: 最低置信度（可选）
            page: 页码
            page_size: 每页数量

        Returns:
            洞察列表和分页信息
        """
        return self._logger.list_insights(insight_type, confidence_min, page, page_size)

    def get_insight(self, insight_id: int) -> dict:
        """获取单条洞察详情。

        Args:
            insight_id: 洞察ID

        Returns:
            洞察详情字典
        """
        return self._logger.get_insight(insight_id)

    def update_insight(
        self,
        insight_id: int,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        confidence: Optional[float] = None,
        applicability: Optional[str] = None,
    ) -> dict:
        """更新洞察信息。

        Args:
            insight_id: 洞察ID
            title: 新标题（可选）
            summary: 新摘要（可选）
            confidence: 新置信度（可选）
            applicability: 适用范围（可选）

        Returns:
            更新后的洞察字典
        """
        return self._logger.update_insight(insight_id, title, summary, confidence, applicability)

    def dashboard(self) -> dict:
        """获取决策情报仪表盘数据。

        Returns:
            仪表盘数据字典
        """
        return self._logger.dashboard()
