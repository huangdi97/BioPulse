"""会话服务模块，管理教练会话的创建、对话日志、评估与反思。"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from sales_coach.app.repositories import ModuleRepository, SessionRepository
from shared.base_service import BaseCrudService


class SessionService(BaseCrudService):
    """教练会话服务，处理会话生命周期、对话记录与评估更新。"""

    def __init__(self, db=None):
        super().__init__(repository_class=SessionRepository, entity_name="Session", db=db)

    def _check_module_exists(self, module_id: int) -> None:
        ModuleRepository(self._connection()).get_active_or_404(module_id)

    def create(self, module_id: int, body, user_id: int) -> dict:
        """创建教练模块下的训练会话。

        Args:
            module_id: 所属训练模块ID。
            body: 会话创建请求体。
            user_id: 创建人用户ID。

        Returns:
            包含新会话ID的字典。

        Raises:
            HTTPException: 当训练模块不存在时由仓储层抛出。
        """
        self._check_module_exists(module_id)
        repo = SessionRepository(self._connection())
        now = datetime.now(timezone.utc).isoformat()
        data = body.model_dump()
        data["module_id"] = module_id
        session_id = repo.create(data, extra={"created_by": user_id, "created_at": now})
        return {"id": session_id}

    def create_digital_human_session(
        self,
        module_id: int,
        body,
        user_id: int,
        session_type: str = "roleplay",
        scenario_id: int = None,
        role: str = None,
    ) -> dict:
        """创建带数字人扩展字段的教练会话。

        Args:
            module_id: 所属训练模块ID。
            body: 会话创建请求体。
            user_id: 创建人用户ID。
            session_type: 会话类型。
            scenario_id: 可选的场景ID。
            role: 可选的扮演角色。

        Returns:
            包含新会话ID的字典。

        Raises:
            HTTPException: 当训练模块不存在时由仓储层抛出。
        """
        self._check_module_exists(module_id)
        repo = SessionRepository(self._connection())
        now = datetime.now(timezone.utc).isoformat()
        data = body.model_dump()
        data["module_id"] = module_id
        data["session_type"] = session_type
        data["scenario_id"] = scenario_id
        data["role"] = role
        data["dialogue_log"] = json.dumps([])
        data["compliance_violations"] = 0
        session_id = repo.create(data, extra={"created_by": user_id, "created_at": now})
        return {"id": session_id}

    def update_dialogue_log(self, session_id: int, entry: dict) -> dict:
        """追加一条数字人会话对话记录。

        Args:
            session_id: 会话ID。
            entry: 需要追加的对话记录。

        Returns:
            更新后的会话字典。

        Raises:
            HTTPException: 当会话不存在时由仓储层抛出。
            json.JSONDecodeError: 当已有对话日志不是合法JSON时抛出。
        """
        repo = SessionRepository(self._connection())
        row = repo.get_session_or_404(session_id)
        log = json.loads(row["dialogue_log"] or "[]")
        log.append(entry)
        repo.update(session_id, {"dialogue_log": json.dumps(log)})
        return dict(repo.get_session_or_404(session_id))

    def get_dialogue_history(self, session_id: int) -> List[Dict[str, Any]]:
        """读取会话完整对话历史。

        Args:
            session_id: 会话ID。

        Returns:
            对话记录列表。

        Raises:
            HTTPException: 当会话不存在时由仓储层抛出。
            json.JSONDecodeError: 当对话日志不是合法JSON时抛出。
        """
        repo = SessionRepository(self._connection())
        row = repo.get_session_or_404(session_id)
        return json.loads(row["dialogue_log"] or "[]")

    def update_assessment(self, session_id: int, assessment: dict) -> dict:
        """更新会话自动评估结果。

        Args:
            session_id: 会话ID。
            assessment: 自动评估结果字典。

        Returns:
            更新后的会话字典。

        Raises:
            HTTPException: 当会话不存在时由仓储层抛出。
        """
        repo = SessionRepository(self._connection())
        repo.get_session_or_404(session_id)
        repo.update(session_id, {"auto_assessment": json.dumps(assessment)})
        return dict(repo.get_session_or_404(session_id))

    def update_reflection(self, session_id: int, report: dict) -> dict:
        """更新会话反思报告。

        Args:
            session_id: 会话ID。
            report: 反思报告字典。

        Returns:
            更新后的会话字典。

        Raises:
            HTTPException: 当会话不存在时由仓储层抛出。
        """
        repo = SessionRepository(self._connection())
        repo.get_session_or_404(session_id)
        repo.update(session_id, {"reflection_report": json.dumps(report)})
        return dict(repo.get_session_or_404(session_id))

    def list(self, module_id: int, page: int, page_size: int) -> tuple:
        """分页列出训练模块下的会话。

        Args:
            module_id: 所属训练模块ID。
            page: 当前页码。
            page_size: 每页数量。

        Returns:
            仓储层分页元组。

        Raises:
            HTTPException: 当训练模块不存在时由仓储层抛出。
        """
        self._check_module_exists(module_id)
        repo = SessionRepository(self._connection())
        return repo.paginate_by_module(module_id, page=page, page_size=page_size)

    def get(self, session_id: int) -> dict:
        """读取单个训练会话。

        Args:
            session_id: 会话ID。

        Returns:
            会话字典。

        Raises:
            HTTPException: 当会话不存在时由仓储层抛出。
        """
        repo = SessionRepository(self._connection())
        return dict(repo.get_session_or_404(session_id))

    def update(self, session_id: int, body) -> dict:
        """更新训练会话字段。

        Args:
            session_id: 会话ID。
            body: 会话更新请求体。

        Returns:
            更新后的会话字典。

        Raises:
            HTTPException: 当会话不存在时由仓储层抛出。
        """
        repo = SessionRepository(self._connection())
        repo.get_session_or_404(session_id)
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(repo.get_session_or_404(session_id))
        repo.update(session_id, updates)
        return dict(repo.get_session_or_404(session_id))

    def delete(self, session_id: int) -> None:
        """硬删除训练会话。

        Args:
            session_id: 会话ID。

        Returns:
            None。

        Raises:
            HTTPException: 当会话不存在时由仓储层抛出。
        """
        repo = SessionRepository(self._connection())
        repo.get_session_or_404(session_id)
        repo.hard_delete(session_id)
