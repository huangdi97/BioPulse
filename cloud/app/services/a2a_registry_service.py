import json
import uuid

from fastapi import HTTPException
from starlette import status

from cloud.app.services.base import BaseService


class A2ARegistryService(BaseService):
    """A2ARegistry 服务类。"""

    def register_agent(self, key, name, type_, description, capabilities, endpoint_url):
        """register_agent 操作。

        Args:
            key: 描述
            name: 描述
            type_: 描述
            description: 描述
            capabilities: 描述
            endpoint_url: 描述
        """
        caps_str = json.dumps(capabilities, ensure_ascii=False)
        existing = self.db.execute("SELECT id FROM agent_registry WHERE agent_key=?", (key,)).fetchone()
        if existing:
            self.db.execute(
                "UPDATE agent_registry SET agent_name=?, agent_type=?, description=?, "
                "capabilities=?, endpoint_url=?, updated_at=CURRENT_TIMESTAMP WHERE agent_key=?",
                (name, type_, description, caps_str, endpoint_url, key),
            )
        else:
            self.db.execute(
                "INSERT INTO agent_registry (agent_key, agent_name, agent_type, description, "
                "capabilities, endpoint_url, status) VALUES (?, ?, ?, ?, ?, ?, 'online')",
                (key, name, type_, description, caps_str, endpoint_url),
            )
        self._event("register", key)
        self.db.commit()
        return self.get_agent(key)

    def get_agent(self, agent_key):
        """get_agent 操作。

        Args:
            agent_key: 描述
        """
        row = self.db.execute("SELECT * FROM agent_registry WHERE agent_key=?", (agent_key,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="agent not found")
        return self._row_to_dict(row)

    def list_agents(self, agent_type=None, status=None, capability=None):
        """list_agents 操作。

        Args:
            agent_type: 描述
            status: 描述
            capability: 描述
        """
        sql = "SELECT * FROM agent_registry WHERE 1=1"
        params = []
        if agent_type:
            sql += " AND agent_type=?"
            params.append(agent_type)
        if status:
            sql += " AND status=?"
            params.append(status)
        if capability:
            sql += " AND capabilities LIKE ?"
            params.append(f'%"{capability}"%')
        sql += " ORDER BY CASE WHEN status='online' THEN 0 ELSE 1 END, created_at DESC"
        rows = self.db.execute(sql, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def heartbeat(self, agent_key):
        """heartbeat 操作。

        Args:
            agent_key: 描述
        """
        self.db.execute(
            "UPDATE agent_registry SET last_heartbeat=CURRENT_TIMESTAMP, status='online' WHERE agent_key=?",
            (agent_key,),
        )
        if self.db.rowcount == 0:
            self.db.commit()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="agent not found")
        self._event("heartbeat", agent_key)
        self.db.commit()
        return self.get_agent(agent_key)

    def update_status(self, agent_key, status_val):
        """update_status 操作。

        Args:
            agent_key: 描述
            status_val: 描述
        """
        if status_val not in ("online", "offline", "paused"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid status")
        self.db.execute(
            "UPDATE agent_registry SET status=?, updated_at=CURRENT_TIMESTAMP WHERE agent_key=?",
            (status_val, agent_key),
        )
        if self.db.rowcount == 0:
            self.db.commit()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="agent not found")
        etype = "deregister" if status_val == "offline" else "status_change"
        self._event(etype, agent_key)
        self.db.commit()
        return self.get_agent(agent_key)

    def submit_task(self, source_key, target_key, task_type, input_data, priority):
        """submit_task 操作。

        Args:
            source_key: 描述
            target_key: 描述
            task_type: 描述
            input_data: 描述
            priority: 描述
        """
        task_id = self._task_id()
        input_str = json.dumps(input_data, ensure_ascii=False)
        self.db.execute(
            "INSERT INTO agent_tasks (task_id, source_agent_key, target_agent_key, task_type, input_data, priority) VALUES (?, ?, ?, ?, ?, ?)",
            (task_id, source_key, target_key, task_type, input_str, priority),
        )
        self._event("routing", source_key, {"task_id": task_id, "target": target_key})
        self.db.commit()
        return self.get_task(task_id)

    def get_task(self, task_id):
        """获取任务。

        Args:
            task_id: 描述
        """
        row = self.db.execute("SELECT * FROM agent_tasks WHERE task_id=?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
        return self._row_to_dict(row)

    def list_tasks(self, status=None, agent_key=None, limit=50):
        """获取任务列表。

        Args:
            status: 描述
            agent_key: 描述
            limit: 描述
        """
        sql = "SELECT * FROM agent_tasks WHERE 1=1"
        params = []
        if status:
            sql += " AND status=?"
            params.append(status)
        if agent_key:
            sql += " AND (source_agent_key=? OR target_agent_key=?)"
            params.extend([agent_key, agent_key])
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = self.db.execute(sql, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def list_events(self, event_type=None, agent_key=None, limit=50):
        """list_events 操作。

        Args:
            event_type: 描述
            agent_key: 描述
            limit: 描述
        """
        sql = "SELECT * FROM agent_network_events WHERE 1=1"
        params = []
        if event_type:
            sql += " AND event_type=?"
            params.append(event_type)
        if agent_key:
            sql += " AND agent_key=?"
            params.append(agent_key)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = self.db.execute(sql, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def _row_to_dict(self, row):
        d = dict(row)
        for col in ("capabilities", "metadata", "input_data", "output_data", "detail"):
            if col in d and isinstance(d[col], str) and d[col]:
                try:
                    d[col] = json.loads(d[col])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d

    def _event(self, etype, agent_key, detail=None):
        detail_str = json.dumps(detail or {}, ensure_ascii=False)
        self.db.execute(
            "INSERT INTO agent_network_events (event_type, agent_key, detail) VALUES (?, ?, ?)",
            (etype, agent_key, detail_str),
        )

    def _task_id(self):
        return f"a2a:{uuid.uuid4().hex}"
