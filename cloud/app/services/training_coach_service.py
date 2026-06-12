"""培训教练服务协调培训评估与推荐功能。"""

from typing import Optional

from cloud.app.services import CoachAssessor
from shared.base_service import BaseService

from .training_coach_recommender import CoachRecommender


class TrainingCoachService(BaseService):
    def __init__(self, db):
        """初始化培训教练服务，创建评估器和推荐器实例。

        参数:
            db: 数据库连接对象。

        返回:
            None
        """
        super().__init__(db)
        self._assessor = CoachAssessor(db)
        self._recommender = CoachRecommender(db)

    def create_module(
        self,
        title: str,
        category: str,
        difficulty: str,
        content: str,
        prerequisites: list,
        passing_score: float,
        estimated_minutes: int,
        created_by: int,
    ) -> dict:
        """创建培训模块。

        参数:
            title: 模块标题。
            category: 模块分类。
            difficulty: 难度等级。
            content: 模块内容。
            prerequisites: 前置条件列表。
            passing_score: 合格分数。
            estimated_minutes: 预计完成分钟数。
            created_by: 创建者用户 ID。

        返回:
            包含新模块信息的字典。
        """
        return self._assessor.create_module(
            title=title,
            category=category,
            difficulty=difficulty,
            content=content,
            prerequisites=prerequisites,
            passing_score=passing_score,
            estimated_minutes=estimated_minutes,
            created_by=created_by,
        )

    def list_modules(self, category: Optional[str] = None, difficulty: Optional[str] = None) -> list:
        """列出培训模块，可按分类和难度筛选。

        参数:
            category: 可选，分类筛选。
            difficulty: 可选，难度筛选。

        返回:
            模块字典列表。
        """
        return self._assessor.list_modules(category=category, difficulty=difficulty)

    def create_session(
        self,
        user_id: int,
        module_id: int,
        score: float,
        passed: int,
        time_spent_seconds: int,
        answers: list,
        feedback: str,
        difficulty_used: str,
    ) -> dict:
        """创建培训会话记录。

        参数:
            user_id: 用户 ID。
            module_id: 模块 ID。
            score: 得分。
            passed: 是否通过（0/1）。
            time_spent_seconds: 花费的秒数。
            answers: 答案列表。
            feedback: 反馈内容。
            difficulty_used: 使用的难度等级。

        返回:
            包含新会话信息的字典。
        """
        return self._assessor.create_session(
            user_id=user_id,
            module_id=module_id,
            score=score,
            passed=passed,
            time_spent_seconds=time_spent_seconds,
            answers=answers,
            feedback=feedback,
            difficulty_used=difficulty_used,
        )

    def list_sessions(
        self,
        user_id: Optional[int] = None,
        module_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """列出培训会话，支持按用户和模块筛选及分页。

        参数:
            user_id: 可选，用户 ID 筛选。
            module_id: 可选，模块 ID 筛选。
            page: 页码，默认为 1。
            page_size: 每页数量，默认为 20。

        返回:
            包含会话列表和分页信息的字典。
        """
        return self._assessor.list_sessions(
            user_id=user_id,
            module_id=module_id,
            page=page,
            page_size=page_size,
        )

    def get_session(self, session_id: int) -> dict:
        """根据会话 ID 获取单个培训会话详情。

        参数:
            session_id: 会话 ID。

        返回:
            包含会话详情的字典。
        """
        return self._assessor.get_session(session_id=session_id)

    def recommend(self, user_id: int) -> dict:
        """为用户推荐培训模块。

        参数:
            user_id: 用户 ID。

        返回:
            包含推荐结果的字典。
        """
        return self._recommender.recommend(user_id=user_id)

    def create_attribution(
        self,
        user_id: int,
        metric_name: str,
        metric_before: float,
        metric_after: float,
        period_days: int,
    ) -> dict:
        """创建培训归因记录。

        参数:
            user_id: 用户 ID。
            metric_name: 指标名称。
            metric_before: 培训前指标值。
            metric_after: 培训后指标值。
            period_days: 统计周期天数。

        返回:
            包含新归因记录的字典。
        """
        return self._assessor.create_attribution(
            user_id=user_id,
            metric_name=metric_name,
            metric_before=metric_before,
            metric_after=metric_after,
            period_days=period_days,
        )

    def list_attributions(self, user_id: Optional[int] = None, metric_name: Optional[str] = None) -> list:
        """列出培训归因记录，可按用户和指标名称筛选。

        参数:
            user_id: 可选，用户 ID 筛选。
            metric_name: 可选，指标名称筛选。

        返回:
            归因记录字典列表。
        """
        return self._assessor.list_attributions(user_id=user_id, metric_name=metric_name)

    def analyze_attribution(self, att_id: int) -> dict:
        """分析指定归因记录的培训效果。

        参数:
            att_id: 归因记录 ID。

        返回:
            包含分析结果的字典。
        """
        return self._assessor.analyze_attribution(att_id=att_id)

    def dashboard(self) -> dict:
        """获取培训教练仪表盘统计数据。

        参数:
            无。

        返回:
            包含仪表盘数据的字典。
        """
        return self._assessor.dashboard()
