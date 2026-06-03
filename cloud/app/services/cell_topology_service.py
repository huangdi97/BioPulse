import json

from cloud.app.services.base import BaseService


class CellTopologyService(BaseService):
    """CellTopology 服务类。"""

    def _row_to_dict(self, row) -> dict:
        d = dict(row)
        for col in ("known_cells", "routing_table", "task_history", "capabilities"):
            if col in d and isinstance(d[col], str) and d[col]:
                try:
                    d[col] = json.loads(d[col])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d

    def analyze_topology(self) -> dict:
        """analyze_topology 操作。

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

        interaction_matrix: dict[str, dict[str, int]] = {}
        cell_routes: dict[str, int] = {}
        agent_types: dict[str, str] = {}

        for cell in cell_list:
            ck = cell["cell_key"]
            interaction_matrix.setdefault(ck, {})
            cell_routes.setdefault(ck, 0)
            agent_types[ck] = cell.get("agent_type", "unknown")
            history = cell.get("task_history", [])
            if isinstance(history, list):
                for entry in history:
                    src = entry.get("source", "")
                    tgt = entry.get("target", "")
                    if src == ck:
                        cell_routes[ck] = cell_routes.get(ck, 0) + 1
                        interaction_matrix[src][tgt] = interaction_matrix.setdefault(src, {}).get(tgt, 0) + 1
                    if tgt == ck:
                        cell_routes[ck] = cell_routes.get(ck, 0) + 1

        edges = []
        for src, targets in interaction_matrix.items():
            for tgt, count in targets.items():
                if count > 0:
                    edges.append({"source": src, "target": tgt, "interaction_count": count})

        sorted_by_traffic = sorted(cell_routes.items(), key=lambda x: x[1], reverse=True)
        hotspots = [{"cell_key": ck, "total_routes": cnt, "agent_type": agent_types.get(ck)} for ck, cnt in sorted_by_traffic[:5] if cnt > 0]

        active_cells = [c for c in cell_list if c["status"] == "active"]
        inactive_cells = [
            {
                "cell_key": c["cell_key"],
                "agent_type": agent_types.get(c["cell_key"]),
                "status": c["status"],
            }
            for c in cell_list
            if c["status"] != "active"
        ]

        isolated = [
            {
                "cell_key": c["cell_key"],
                "agent_type": agent_types.get(c["cell_key"]),
            }
            for c in active_cells
            if all(tgt != c["cell_key"] and src != c["cell_key"] for e in edges for src, tgt in [(e["source"], e["target"])])
            and cell_routes.get(c["cell_key"], 0) == 0
        ]

        return {
            "total_cells": len(cell_list),
            "active_cells": len(active_cells),
            "inactive_cells": inactive_cells,
            "isolated_cells": isolated,
            "hotspots": hotspots,
            "interaction_edges": edges,
            "agent_type_distribution": {t: list(agent_types.values()).count(t) for t in set(agent_types.values())},
        }

    def suggest_optimization(self) -> dict:
        """suggest_optimization 操作。

        Returns:
            描述
        """
        analysis = self.analyze_topology()
        suggestions: list[dict] = []

        interaction_map: dict[tuple[str, str], int] = {}
        for e in analysis.get("interaction_edges", []):
            key = (e["source"], e["target"])
            interaction_map[key] = e["interaction_count"]
            rev_key = (e["target"], e["source"])
            interaction_map[rev_key] = interaction_map.get(rev_key, 0) + e["interaction_count"]

        seen_pairs: set[tuple[str, str]] = set()
        for (src, tgt), count in sorted(interaction_map.items(), key=lambda x: -x[1]):
            pair = tuple(sorted([src, tgt]))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            if count >= 3:
                suggestions.append(
                    {
                        "type": "merge",
                        "reason": f"high mutual interaction ({count} routes)",
                        "cells": [src, tgt],
                        "priority": "high" if count >= 5 else "medium",
                    }
                )

        for h in analysis.get("hotspots", []):
            if h["total_routes"] >= 5:
                suggestions.append(
                    {
                        "type": "split",
                        "reason": f"excessive routing load ({h['total_routes']} routes)",
                        "cells": [h["cell_key"]],
                        "priority": "high" if h["total_routes"] >= 10 else "medium",
                    }
                )

        edges = analysis.get("interaction_edges", [])
        source_targets: dict[str, set[str]] = {}
        for e in edges:
            source_targets.setdefault(e["source"], set()).add(e["target"])
        for src, targets in source_targets.items():
            if len(targets) >= 4:
                suggestions.append(
                    {
                        "type": "reroute",
                        "reason": f"hub cell routes to {len(targets)} peers, consider load-balanced routing",
                        "cells": [src],
                        "priority": "medium",
                    }
                )

        for c in analysis.get("isolated_cells", []):
            suggestions.append(
                {
                    "type": "remove",
                    "reason": "cell has zero interaction with any peer",
                    "cells": [c["cell_key"]],
                    "priority": "low",
                }
            )

        return {
            "suggestions": suggestions,
            "total_suggestions": len(suggestions),
            "based_on_analysis": {
                "total_cells": analysis["total_cells"],
                "active_cells": analysis["active_cells"],
            },
        }
