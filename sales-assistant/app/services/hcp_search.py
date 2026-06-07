"""HCP 图谱查询相关 mixin。"""

from typing import Optional


class HcpSearchMixin:
    def get_graph(self, hcp_id: Optional[int], product_id: Optional[int]) -> dict:
        hcp_cond, hcp_params = ("AND h.id = ?", [hcp_id]) if hcp_id else ("", [])
        hcps = self.db.execute(
            f"SELECT id, name, COALESCE(tier,'C') AS tier, hospital FROM hcp WHERE is_active = 1 {hcp_cond}",
            hcp_params,
        ).fetchall()
        if hcp_id:
            prods = self.db.execute(
                "SELECT DISTINCT p.id, p.name, p.company FROM product p "
                "JOIN hcp_product_relation r ON p.id = r.product_id "
                "WHERE p.is_active = 1 AND r.is_active = 1 AND r.hcp_id = ?",
                (hcp_id,),
            ).fetchall()
        elif product_id:
            prods = self.db.execute(
                "SELECT id, name, company FROM product WHERE is_active = 1 AND id = ?",
                (product_id,),
            ).fetchall()
        else:
            prods = self.db.execute("SELECT id, name, company FROM product WHERE is_active = 1").fetchall()
        hcp_ids = [h["id"] for h in hcps]
        if hcp_ids:
            placeholders = ",".join("?" * len(hcp_ids))
            edges = self.db.execute(
                f"SELECT hcp_id, product_id, relation_type, strength FROM hcp_product_relation WHERE is_active = 1 AND hcp_id IN ({placeholders})",
                hcp_ids,
            ).fetchall()
        else:
            edges = []
        nodes = [{"id": f"hcp:{h['id']}", "type": "hcp", "label": h["name"], "tier": h["tier"], "hospital": h["hospital"]} for h in hcps]
        nodes += [{"id": f"product:{p['id']}", "type": "product", "label": p["name"], "company": p["company"]} for p in prods]
        edge_list = [
            {"source": f"hcp:{e['hcp_id']}", "target": f"product:{e['product_id']}", "type": e["relation_type"], "strength": e["strength"]}
            for e in edges
        ]
        return {"nodes": nodes, "edges": edge_list}
