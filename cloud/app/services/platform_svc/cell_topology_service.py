"""Cell 拓扑服务，分析 Agent 网络拓扑结构并生成优化建议。"""

import logging

from shared.base_service import BaseService
from shared.datetime_utils import row_to_dict

logger = logging.getLogger(__name__)


class CellTopologyService(BaseService):
    """CellTopology 服务类。"""

    def _build_interaction_data(self, cell_list: list) -> tuple:
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
        return interaction_matrix, cell_routes, agent_types

    def _find_isolated_cells(self, cell_list: list, edges: list, cell_routes: dict) -> list:
        active_cells = [c for c in cell_list if c["status"] == "active"]
        return [
            {"cell_key": c["cell_key"], "agent_type": c.get("agent_type", "unknown")}
            for c in active_cells
            if all(tgt != c["cell_key"] and src != c["cell_key"] for e in edges for src, tgt in [(e["source"], e["target"])])
            and cell_routes.get(c["cell_key"], 0) == 0
        ]

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
        cell_list = [row_to_dict(r, "known_cells", "routing_table", "task_history", "capabilities") for r in cells]

        interaction_matrix, cell_routes, agent_types = self._build_interaction_data(cell_list)

        edges = []
        for src, targets in interaction_matrix.items():
            for tgt, count in targets.items():
                if count > 0:
                    edges.append({"source": src, "target": tgt, "interaction_count": count})

        sorted_by_traffic = sorted(cell_routes.items(), key=lambda x: x[1], reverse=True)
        hotspots = [{"cell_key": ck, "total_routes": cnt, "agent_type": agent_types.get(ck)} for ck, cnt in sorted_by_traffic[:5] if cnt > 0]

        active_cells = [c for c in cell_list if c["status"] == "active"]
        inactive_cells = [
            {"cell_key": c["cell_key"], "agent_type": agent_types.get(c["cell_key"]), "status": c["status"]}
            for c in cell_list
            if c["status"] != "active"
        ]

        isolated = self._find_isolated_cells(cell_list, edges, cell_routes)

        return {
            "total_cells": len(cell_list),
            "active_cells": len(active_cells),
            "inactive_cells": inactive_cells,
            "isolated_cells": isolated,
            "hotspots": hotspots,
            "interaction_edges": edges,
            "agent_type_distribution": {t: list(agent_types.values()).count(t) for t in set(agent_types.values())},
        }

    def _build_interaction_map(self, edges: list) -> dict[tuple[str, str], int]:
        interaction_map: dict[tuple[str, str], int] = {}
        for e in edges:
            key = (e["source"], e["target"])
            interaction_map[key] = e["interaction_count"]
            rev_key = (e["target"], e["source"])
            interaction_map[rev_key] = interaction_map.get(rev_key, 0) + e["interaction_count"]
        return interaction_map

    def _generate_merge_suggestions(self, interaction_map: dict) -> list[dict]:
        suggestions: list[dict] = []
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
        return suggestions

    def suggest_optimization(self) -> dict:
        """suggest_optimization 操作。

        Returns:
            描述
        """
        analysis = self.analyze_topology()
        suggestions: list[dict] = []

        interaction_map = self._build_interaction_map(analysis.get("interaction_edges", []))
        suggestions.extend(self._generate_merge_suggestions(interaction_map))

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
