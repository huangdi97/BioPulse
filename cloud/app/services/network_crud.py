"""网络CRUD模块，负责智能体细胞网络的注册、发现与拓扑管理。"""

import json
import logging
import uuid

from fastapi import HTTPException
from starlette import status

logger = logging.getLogger(__name__)


class NetworkCrudMixin:
    """网络CRUD混入类，提供智能体细胞的注册、自动发现与拓扑查询。"""

    def register_cell(self, agent_instance_key: str) -> dict:
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
            "INSERT INTO agent_cell_network (cell_key, agent_instance_key, known_cells, routing_table) VALUES (?, ?, '[]', '{}')",
            (cell_key, agent_instance_key),
        )
        self.db.commit()
        return self._get_cell(cell_key)

    def auto_discover(self) -> dict:
        online_agents = self.db.execute("SELECT agent_key FROM agent_registry WHERE status='online'").fetchall()

        registered = 0
        failed: list[dict] = []
        cells: list[str] = []

        for agent in online_agents:
            agent_key = agent["agent_key"]
            existing = self.db.execute(
                "SELECT id FROM agent_cell_network WHERE agent_instance_key=?",
                (agent_key,),
            ).fetchone()
            if existing:
                continue

            try:
                cell_key = f"cell:{uuid.uuid4().hex}"
                self.db.execute(
                    "INSERT INTO agent_cell_network (cell_key, agent_instance_key, known_cells, routing_table) VALUES (?, ?, '[]', '{}')",
                    (cell_key, agent_key),
                )
                registered += 1
                cells.append(cell_key)
            except Exception as e:
                failed.append({"agent_instance_key": agent_key, "error": str(e)})

        self.db.commit()

        return {
            "total_online_agents": len(online_agents),
            "newly_registered": registered,
            "registered_cells": cells,
            "failed": failed,
            "failed_count": len(failed),
        }

    def discover_cells(self, capability: str | None = None) -> list:
        sql = "SELECT c.* FROM agent_cell_network c LEFT JOIN agent_registry r ON c.agent_instance_key = r.agent_key WHERE c.status='active'"
        params: list = []
        if capability:
            sql += " AND r.capabilities LIKE ?"
            params.append(f'%"{capability}"%')
        sql += " ORDER BY c.created_at DESC"
        rows = self.db.execute(sql, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_network_topology(self) -> dict:
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

    def get_topology_for_visualization(self) -> dict:
        cells = self.db.execute(
            "SELECT c.*, r.agent_name, r.agent_type, r.capabilities "
            "FROM agent_cell_network c "
            "LEFT JOIN agent_registry r ON c.agent_instance_key = r.agent_key "
            "ORDER BY c.created_at DESC"
        ).fetchall()
        cell_list = [self._row_to_dict(r) for r in cells]

        nodes: list[dict] = []
        edges: list[dict] = []
        seen_edges: set[tuple[str, str]] = set()

        for cell in cell_list:
            nodes.append(
                {
                    "id": cell["cell_key"],
                    "label": cell.get("agent_name") or cell.get("agent_instance_key", ""),
                    "type": cell.get("agent_type", "agent"),
                    "status": cell["status"],
                    "capabilities": cell.get("capabilities"),
                }
            )
            known = json.loads(cell.get("known_cells", "[]"))
            for target in known:
                edge_key = (cell["cell_key"], target)
                reverse_key = (target, cell["cell_key"])
                if edge_key not in seen_edges and reverse_key not in seen_edges:
                    seen_edges.add(edge_key)
                    edges.append(
                        {
                            "source": cell["cell_key"],
                            "target": target,
                        }
                    )

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }

    def health_check(self) -> dict:
        try:
            self.db.execute("SELECT 1 FROM agent_cell_network LIMIT 1")
        except Exception:
            return {
                "status": "unhealthy",
                "db_connected": False,
                "total_cells": 0,
                "active_cells": 0,
                "detail": "database connection failed",
            }

        total = self.db.execute("SELECT COUNT(*) as count FROM agent_cell_network").fetchone()["count"]
        active = self.db.execute("SELECT COUNT(*) as count FROM agent_cell_network WHERE status='active'").fetchone()["count"]

        return {
            "status": "healthy",
            "db_connected": True,
            "total_cells": total,
            "active_cells": active,
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
                    logger.warning("Failed to parse network cell JSON field '%s'", col, exc_info=True)
        return d
