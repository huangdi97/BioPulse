"""智能体执行任务、市场、管线、角色、技能、编排模板等数据访问层。"""

from cloud.shared.columns import (
    TABLE_AGENT_EXECUTION_TASKS_COLS,
    TABLE_AGENT_MARKETPLACE_COLS,
    TABLE_AGENT_PIPELINES_COLS,
    TABLE_AGENT_ROLES_COLS,
    TABLE_AGENT_SKILLS_COLS,
    TABLE_ORCHESTRATION_TEMPLATES_COLS,
    TABLE_PIPELINE_RUNS_COLS,
    TABLE_PIPELINE_STEP_RUNS_COLS,
    TABLE_PIPELINE_STEPS_COLS,
)
from cloud.shared.repository import BaseRepository


class AgentExecutionTasksRepository(BaseRepository):
    """智能体执行任务表。"""

    def __init__(self, db):
        super().__init__(db, "agent_execution_tasks", TABLE_AGENT_EXECUTION_TASKS_COLS)

    def get_by_task_id(self, task_id: str):
        placeholders = ", ".join(self.cols)
        query = f"SELECT {placeholders} FROM {self.table_name} WHERE task_id = ?"
        cursor = self.db.execute(query, (task_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


class AgentMarketplaceRepository(BaseRepository):
    """智能体市场表。"""

    def __init__(self, db):
        super().__init__(db, "agent_marketplace", TABLE_AGENT_MARKETPLACE_COLS)

    def list_filtered(self, category=None, price_model=None, enabled=None) -> list:
        placeholders = ", ".join(self.cols)
        conditions, params = [], []
        if category:
            conditions.append("category = ?")
            params.append(category)
        if price_model:
            conditions.append("price_model = ?")
            params.append(price_model)
        if enabled is not None:
            conditions.append("enabled = ?")
            params.append(enabled)
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name}{where} ORDER BY rating DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]


class AgentPipelinesRepository(BaseRepository):
    """智能体管线表。"""

    def __init__(self, db):
        super().__init__(db, "agent_pipelines", TABLE_AGENT_PIPELINES_COLS)


class AgentRolesRepository(BaseRepository):
    """智能体角色表。"""

    def __init__(self, db):
        super().__init__(db, "agent_roles", TABLE_AGENT_ROLES_COLS)

    def list_active(self, limit: int = 5) -> list:
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE is_active=1 LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_system_prompt(self, role_id: int):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(f"SELECT {placeholders} FROM {self.table_name} WHERE id=?", (role_id,)).fetchone()
        return dict(row) if row else None

    def get_by_id(self, role_id: int):
        return super().get_by_id(role_id)


class AgentSkillsRepository(BaseRepository):
    """智能体技能表。"""

    def __init__(self, db):
        super().__init__(db, "agent_skills", TABLE_AGENT_SKILLS_COLS)


class PipelineRunsRepository(BaseRepository):
    """管线运行记录表。"""

    def __init__(self, db):
        super().__init__(db, "pipeline_runs", TABLE_PIPELINE_RUNS_COLS)


class PipelineStepRunsRepository(BaseRepository):
    """管线步骤运行记录表。"""

    def __init__(self, db):
        super().__init__(db, "pipeline_step_runs", TABLE_PIPELINE_STEP_RUNS_COLS)


class PipelineStepsRepository(BaseRepository):
    """管线步骤定义表。"""

    def __init__(self, db):
        super().__init__(db, "pipeline_steps", TABLE_PIPELINE_STEPS_COLS)


class OrchestrationTemplatesRepository(BaseRepository):
    """编排模板表。"""

    def __init__(self, db):
        super().__init__(db, "orchestration_templates", TABLE_ORCHESTRATION_TEMPLATES_COLS)
