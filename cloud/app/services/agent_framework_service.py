"""Agent 框架服务，管理角色模板与实例的生命周期（创建、启停、心跳）。"""

import json
import logging

from fastapi import HTTPException
from starlette import status

from cloud.app.services.base import BaseService

logger = logging.getLogger(__name__)


class AgentFrameworkService(BaseService):
    """Agent 框架服务，提供模板管理、实例生命周期与 A2A 自动注册。"""

    def list_templates(self, domain=None):
        """列出 Agent 角色模板。

        Args:
            domain: 按领域筛选

        Returns:
            模板列表
        """
        sql = "SELECT * FROM agent_role_templates WHERE 1=1"
        params = []
        if domain:
            sql += " AND domain=?"
            params.append(domain)
        rows = self.db.execute(sql, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_template(self, template_key):
        """获取指定模板。

        Args:
            template_key: 模板键
        """
        row = self.db.execute("SELECT * FROM agent_role_templates WHERE template_key=?", (template_key,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="template not found")
        return self._row_to_dict(row)

    def create_template(self, key, name, description, domain, capabilities, default_config, triggers, endpoints):
        """创建角色模板。

        Args:
            key: 模板唯一键
            name: 名称
            description: 描述
            domain: 领域
            capabilities: 能力列表
            default_config: 默认配置
            triggers: 触发器配置
            endpoints: 端点配置
        """
        self.db.execute(
            "INSERT INTO agent_role_templates (template_key, name, description, domain, capabilities, default_config, triggers, endpoints) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                key,
                name,
                description,
                domain,
                json.dumps(capabilities, ensure_ascii=False),
                json.dumps(default_config, ensure_ascii=False),
                json.dumps(triggers, ensure_ascii=False),
                json.dumps(endpoints, ensure_ascii=False),
            ),
        )
        self.db.commit()
        return self.get_template(key)

    def list_instances(self, status=None, template_key=None):
        """列出 Agent 实例。

        Args:
            status: 按状态筛选
            template_key: 按模板键筛选

        Returns:
            实例列表
        """
        sql = "SELECT * FROM agent_instances WHERE 1=1"
        params = []
        if status:
            sql += " AND status=?"
            params.append(status)
        if template_key:
            sql += " AND template_key=?"
            params.append(template_key)
        rows = self.db.execute(sql, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_instance(self, instance_key):
        """获取指定实例。

        Args:
            instance_key: 实例键
        """
        row = self.db.execute("SELECT * FROM agent_instances WHERE instance_key=?", (instance_key,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="instance not found")
        return self._row_to_dict(row)

    def create_instance(self, instance_key, template_key, display_name, bind_to_end, config_overrides):
        """创建 Agent 实例，可选自动注册到 A2A。

        Args:
            instance_key: 实例唯一键
            template_key: 关联模板键
            display_name: 显示名称
            bind_to_end: 绑定端点
            config_overrides: 配置覆盖
        """
        template = self.get_template(template_key)
        self.db.execute(
            "INSERT INTO agent_instances (instance_key, template_key, display_name, bind_to_end, config_overrides) VALUES (?, ?, ?, ?, ?)",
            (instance_key, template_key, display_name, bind_to_end, json.dumps(config_overrides, ensure_ascii=False)),
        )
        self.db.commit()
        instance = self.get_instance(instance_key)
        default_config = template.get("default_config", {})
        if default_config.get("auto_register", False):
            a2a = self._a2a_service()
            agent_key = f"agent:{instance_key}"
            caps = template.get("capabilities", [])
            a2a.register_agent(
                key=agent_key,
                name=display_name or instance_key,
                type_="agent_framework",
                description=template.get("description", ""),
                capabilities=caps,
                endpoint_url="",
            )
            self.db.execute(
                "UPDATE agent_instances SET a2a_agent_key=? WHERE instance_key=?",
                (agent_key, instance_key),
            )
            self.db.commit()
            instance = self.get_instance(instance_key)
        return instance

    def start_instance(self, instance_key):
        """启动实例并注册到 A2A。

        Args:
            instance_key: 实例键
        """
        instance = self.get_instance(instance_key)
        if instance.get("status") == "running":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="instance already running")
        template = self.get_template(instance["template_key"])
        agent_key = instance.get("a2a_agent_key") or f"agent:{instance_key}"
        a2a = self._a2a_service()
        a2a.register_agent(
            key=agent_key,
            name=instance.get("display_name") or instance_key,
            type_="agent_framework",
            description=template.get("description", ""),
            capabilities=template.get("capabilities", []),
            endpoint_url="",
        )
        self.db.execute(
            "UPDATE agent_instances SET status='running', a2a_agent_key=?, last_active_at=CURRENT_TIMESTAMP WHERE instance_key=?",
            (agent_key, instance_key),
        )
        self.db.commit()
        a2a.heartbeat(agent_key)
        return self.get_instance(instance_key)

    def stop_instance(self, instance_key):
        """停止实例并更新 A2A 状态。

        Args:
            instance_key: 实例键
        """
        instance = self.get_instance(instance_key)
        self.db.execute(
            "UPDATE agent_instances SET status='stopped' WHERE instance_key=?",
            (instance_key,),
        )
        self.db.commit()
        agent_key = instance.get("a2a_agent_key")
        if agent_key:
            self._a2a_service().update_status(agent_key, "offline")
        return self.get_instance(instance_key)

    def heartbeat_instance(self, instance_key):
        """发送实例心跳并同步 A2A。

        Args:
            instance_key: 实例键
        """
        instance = self.get_instance(instance_key)
        self.db.execute(
            "UPDATE agent_instances SET last_active_at=CURRENT_TIMESTAMP WHERE instance_key=?",
            (instance_key,),
        )
        self.db.commit()
        agent_key = instance.get("a2a_agent_key")
        if agent_key:
            self._a2a_service().heartbeat(agent_key)
        row = self.db.execute("SELECT last_active_at FROM agent_instances WHERE instance_key=?", (instance_key,)).fetchone()
        return {"status": instance.get("status"), "last_active_at": row["last_active_at"]}

    def _row_to_dict(self, row):
        """将数据库行对象转换为字典，自动解析 JSON 字段。

        Args:
            row: 数据库行对象。

        Returns:
            字典，其中 capabilities, default_config, triggers, endpoints, config_overrides, metrics 字段已从 JSON 解析。
        """
        d = dict(row)
        for col in ("capabilities", "default_config", "triggers", "endpoints", "config_overrides", "metrics"):
            if col in d and isinstance(d[col], str) and d[col]:
                try:
                    d[col] = json.loads(d[col])
                except (json.JSONDecodeError, TypeError):
                    logger.warning("Failed to parse agent framework JSON field '%s'", col, exc_info=True)
        return d

    def _a2a_service(self):
        """返回 A2aRegistryService 实例，用于 Agent 自动注册与心跳同步。

        Returns:
            A2aRegistryService 实例。
        """
        from cloud.app.services.a2a_registry_service import A2aRegistryService

        return A2aRegistryService(db=self.db)
