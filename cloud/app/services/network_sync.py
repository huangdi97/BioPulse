import json
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from starlette import status


class NetworkSyncMixin:
    def route_to_cell(self, source_key: str, target_key: str, task_data: dict) -> dict:
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
        all_cells = self.db.execute(
            "SELECT cell_key, agent_instance_key, status FROM agent_cell_network WHERE status='active' ORDER BY created_at DESC"
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
