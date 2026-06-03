import json

from fastapi import HTTPException
from starlette import status

from cloud.app.services.base import BaseService


class AgentFrameworkService(BaseService):
    """AgentFramework 服务类。"""

    def list_templates(self, domain=None):
        """list_templates 操作。

        Args:
            domain: 描述
        """
        sql = "SELECT * FROM agent_role_templates WHERE 1=1"
        params = []
        if domain:
            sql += " AND domain=?"
            params.append(domain)
        rows = self.db.execute(sql, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_template(self, template_key):
        """get_template 操作。

        Args:
            template_key: 描述
        """
        row = self.db.execute("SELECT * FROM agent_role_templates WHERE template_key=?", (template_key,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="template not found")
        return self._row_to_dict(row)

    def create_template(self, key, name, description, domain, capabilities, default_config, triggers, endpoints):
        """create_template 操作。

        Args:
            key: 描述
            name: 描述
            description: 描述
            domain: 描述
            capabilities: 描述
            default_config: 描述
            triggers: 描述
            endpoints: 描述
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
        """list_instances 操作。

        Args:
            status: 描述
            template_key: 描述
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
        """get_instance 操作。

        Args:
            instance_key: 描述
        """
        row = self.db.execute("SELECT * FROM agent_instances WHERE instance_key=?", (instance_key,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="instance not found")
        return self._row_to_dict(row)

    def create_instance(self, instance_key, template_key, display_name, bind_to_end, config_overrides):
        """create_instance 操作。

        Args:
            instance_key: 描述
            template_key: 描述
            display_name: 描述
            bind_to_end: 描述
            config_overrides: 描述
        """
        template = self.get_template(template_key)
        self.db.execute(
            "INSERT INTO agent_instances (instance_key, template_key, display_name, bind_to_end, config_overrides) "
            "VALUES (?, ?, ?, ?, ?)",
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
        """start_instance 操作。

        Args:
            instance_key: 描述
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
        """stop_instance 操作。

        Args:
            instance_key: 描述
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
        """heartbeat_instance 操作。

        Args:
            instance_key: 描述
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
        row = self.db.execute(
            "SELECT last_active_at FROM agent_instances WHERE instance_key=?", (instance_key,)
        ).fetchone()
        return {"status": instance.get("status"), "last_active_at": row["last_active_at"]}

    def _row_to_dict(self, row):
        d = dict(row)
        for col in ("capabilities", "default_config", "triggers", "endpoints", "config_overrides", "metrics"):
            if col in d and isinstance(d[col], str) and d[col]:
                try:
                    d[col] = json.loads(d[col])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d

    def _a2a_service(self):
        from cloud.app.services.a2a_registry_service import A2ARegistryService

        return A2ARegistryService(db=self.db)
