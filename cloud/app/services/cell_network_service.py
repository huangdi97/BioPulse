import json
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from starlette import status

from cloud.app.services.base import BaseService


class CellNetworkService(BaseService):
    """CellNetwork 服务类。"""

    def register_cell(self, agent_instance_key: str) -> dict:
        """register_cell 操作。

        Args:
            agent_instance_key: 描述

        Returns:
            描述
        """
        cell_key = f"cell:{uuid.uuid4().hex}"
        existing = self.db.execute(
            "SELECT id FROM agent_registry WHERE agent_key=? AND status='online'",
            (agent_instance_key,),
        ).fetchone()
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="agent instance not found or not online",
            )
        dup = self.db.execute(
            "SELECT id FROM agent_cell_network WHERE agent_instance_key=?",
            (agent_instance_key,),
        ).fetchone()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="agent already registered as a cell",
            )
        self.db.execute(
            "INSERT INTO agent_cell_network "
            "(cell_key, agent_instance_key, known_cells, routing_table) "
            "VALUES (?, ?, '[]', '{}')",
            (cell_key, agent_instance_key),
        )
        self.db.commit()
        return self._get_cell(cell_key)

    def discover_cells(self, capability: str | None = None) -> list:
        """discover_cells 操作。

        Args:
            capability: 描述

        Returns:
            描述
        """
        sql = (
            "SELECT c.* FROM agent_cell_network c "
            "LEFT JOIN agent_registry r ON c.agent_instance_key = r.agent_key "
            "WHERE c.status='active'"
        )
        params: list = []
        if capability:
            sql += " AND r.capabilities LIKE ?"
            params.append(f'%"{capability}"%')
        sql += " ORDER BY c.created_at DESC"
        rows = self.db.execute(sql, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def route_to_cell(self, source_key: str, target_key: str, task_data: dict) -> dict:
        """route_to_cell 操作。

        Args:
            source_key: 描述
            target_key: 描述
            task_data: 描述

        Returns:
            描述
        """
        source = self._get_cell(source_key)
        target = self._get_cell(target_key)
        if source["status"] != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="source cell is not active",
            )
        if target["status"] != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="target cell is not active",
            )
        task_id = f"route:{uuid.uuid4().hex}"
        history = json.loads(source.get("task_history", "[]"))
        entry = {
            "task_id": task_id,
            "source": source_key,
            "target": target_key,
            "data": task_data,
            "status": "routed",
            "routed_at": datetime.now(timezone.utc).isoformat(),
        }
        history.append(entry)
        self.db.execute(
            "UPDATE agent_cell_network SET task_history=? WHERE cell_key=?",
            (json.dumps(history, ensure_ascii=False), source_key),
        )
        target_history = json.loads(target.get("task_history", "[]"))
        target_entry = {
            "task_id": task_id,
            "source": source_key,
            "target": target_key,
            "data": task_data,
            "status": "received",
            "routed_at": datetime.now(timezone.utc).isoformat(),
        }
        target_history.append(target_entry)
        self.db.execute(
            "UPDATE agent_cell_network SET task_history=? WHERE cell_key=?",
            (json.dumps(target_history, ensure_ascii=False), target_key),
        )
        self.db.commit()
        return entry

    def sync_routing_table(self, cell_key: str) -> dict:
        """sync_routing_table 操作。

        Args:
            cell_key: 描述

        Returns:
            描述
        """
        cell = self._get_cell(cell_key)
        all_cells = self.db.execute(
            "SELECT cell_key, agent_instance_key, status FROM agent_cell_network "
            "WHERE status='active' ORDER BY created_at DESC"
        ).fetchall()
        routing_table: dict[str, str] = {}
        known_cells: list[str] = []
        for row in all_cells:
            d = dict(row)
            if d["cell_key"] != cell_key:
                routing_table[d["cell_key"]] = d["agent_instance_key"]
                known_cells.append(d["cell_key"])
        now = datetime.now(timezone.utc).isoformat()
        self.db.execute(
            "UPDATE agent_cell_network SET known_cells=?, routing_table=?, last_sync_at=? WHERE cell_key=?",
            (
                json.dumps(known_cells, ensure_ascii=False),
                json.dumps(routing_table, ensure_ascii=False),
                now,
                cell_key,
            ),
        )
        self.db.commit()
        return self._get_cell(cell_key)

    def get_network_topology(self) -> dict:
        """get_network_topology 操作。

        Returns:
            描述
        """
        cells = self.db.execute(
            "SELECT c.*, r.agent_name, r.agent_type, r.capabilities "
            "FROM agent_cell_network c "
            "LEFT JOIN agent_registry r ON c.agent_instance_key = r.agent_key "
            "ORDER BY c.created_at DESC"
        ).fetchall()
        cell_list = [self._row_to_dict(r) for r in cells]
        routing_map: dict[str, list[str]] = {}
        for cell in cell_list:
            known = json.loads(cell.get("known_cells", "[]"))
            routing_map[cell["cell_key"]] = known
        return {
            "total_cells": len(cell_list),
            "active_cells": sum(1 for c in cell_list if c["status"] == "active"),
            "cells": cell_list,
            "routing_map": routing_map,
        }

    def _get_cell(self, cell_key: str) -> dict:
        row = self.db.execute("SELECT * FROM agent_cell_network WHERE cell_key=?", (cell_key,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="cell not found")
        return self._row_to_dict(row)

    def _row_to_dict(self, row) -> dict:
        d = dict(row)
        for col in ("known_cells", "routing_table", "task_history", "capabilities"):
            if col in d and isinstance(d[col], str) and d[col]:
                try:
                    d[col] = json.loads(d[col])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d
