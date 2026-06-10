"""HCP/Buyer relationship graph — track past interactions, purchase history, decision chain."""

from __future__ import annotations

from typing import Any


class RelationshipGraph:
    """In-memory relationship graph for HCP/Buyer entities."""

    def __init__(self):
        self._nodes: dict[str, dict[str, Any]] = {}
        self._edges: list[dict[str, Any]] = []

    def add_node(self, entity_id: str, entity_type: str, name: str, attrs: dict[str, Any] | None = None) -> None:
        """Add or update an entity node."""
        self._nodes[entity_id] = {
            "id": entity_id,
            "type": entity_type,
            "name": name,
            "attrs": attrs or {},
        }

    def add_edge(self, source: str, target: str, relation: str, attrs: dict[str, Any] | None = None) -> None:
        """Add a relationship edge between two nodes."""
        self._edges.append({"source": source, "target": target, "relation": relation, "attrs": attrs or {}})

    def add_interaction(self, hcp_id: str, rep_id: str, interaction_type: str, notes: str = "") -> None:
        """Record a past interaction event."""
        self.add_edge(hcp_id, rep_id, "interacted", {"type": interaction_type, "notes": notes})

    def add_purchase(self, hcp_id: str, product: str, amount: float, date: str = "") -> None:
        """Record a purchase event."""
        self.add_edge(hcp_id, f"product:{product}", "purchased", {"amount": amount, "date": date})

    def get_node(self, entity_id: str) -> dict[str, Any] | None:
        return self._nodes.get(entity_id)

    def get_connections(self, entity_id: str) -> list[dict[str, Any]]:
        """Get all edges connected to an entity."""
        return [e for e in self._edges if e["source"] == entity_id or e["target"] == entity_id]

    def get_decision_chain(self, hcp_id: str) -> list[dict[str, Any]]:
        """Trace the decision chain for an HCP."""
        chain = []
        for edge in self._edges:
            if edge["source"] == hcp_id and edge["relation"] in {"reports_to", "influences", "approves"}:
                chain.append(edge)
        return chain

    def to_dict(self) -> dict[str, Any]:
        return {"nodes": self._nodes, "edges": self._edges}
