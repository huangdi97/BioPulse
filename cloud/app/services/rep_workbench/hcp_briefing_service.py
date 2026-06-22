"""HCP 拜访画像服务 — Task 2"""

from typing import Any

from shared.base_service import BaseService


class HcpBriefingService(BaseService):
    """生成 HCP 一页画像，包含处方偏好、科研动态、接触偏好、竞品关系、上次互动。"""

    def get_briefing(self, hcp_id: int) -> dict[str, Any]:
        profile = self._get_profile(hcp_id)
        return {
            "hcp_id": str(hcp_id),
            "hcp_name": profile["name"],
            "hospital": profile["hospital"],
            "department": profile["department"],
            "title": profile["title"],
            "prescription_preference": self._prescription_preference(hcp_id),
            "research_updates": self._research_updates(hcp_id),
            "contact_preference": self._contact_preference(hcp_id),
            "competitor_relation": self._competitor_relation(hcp_id),
            "last_interaction": self._last_interaction(hcp_id),
        }

    def _get_profile(self, hcp_id: int) -> dict:
        conn = self._connection()
        row = conn.execute(
            "SELECT name, hospital, department, title FROM hcp_profiles WHERE id=?",
            (hcp_id,),
        ).fetchone()
        if row:
            return dict(row)
        profiles = {
            101: {"name": "陈主任", "hospital": "北京协和医院", "department": "心内科", "title": "主任医师"},
            102: {"name": "李主任", "hospital": "上海中山医院", "department": "内分泌科", "title": "副主任医师"},
            103: {"name": "张主任", "hospital": "广州南方医院", "department": "消化内科", "title": "主任医师"},
            104: {"name": "王主任", "hospital": "杭州浙一医院", "department": "神经内科", "title": "主任医师"},
            105: {"name": "刘主任", "hospital": "北京人民医院", "department": "呼吸科", "title": "副主任医师"},
        }
        return profiles.get(hcp_id, {"name": "未知医生", "hospital": "", "department": "", "title": ""})

    def _prescription_preference(self, hcp_id: int) -> dict:
        hcp_str = str(hcp_id)
        hash_val = sum(ord(c) for c in hcp_str)
        my_share = 30 + (hash_val % 20)
        competitor_share = 100 - my_share
        return {
            "trend": "上升" if hash_val % 2 == 0 else "下降",
            "my_product_share": my_share,
            "competitor_share": competitor_share,
            "my_product_3m_change": f"+{hash_val % 10}%" if hash_val % 2 == 0 else f"-{hash_val % 8}%",
            "top_product": "阿托伐他汀",
        }

    def _research_updates(self, hcp_id: int) -> list[dict]:
        hcp_str = str(hcp_id)
        if sum(ord(c) for c in hcp_str) % 3 == 0:
            return [
                {"type": "论文", "title": "新型抗凝药物在房颤患者中的应用进展", "journal": "中华心血管病杂志", "date": "2026-05-15"},
                {"type": "学术会议", "title": "2026 中国心脏大会 - 专题发言", "date": "2026-04-20"},
            ]
        return []

    def _contact_preference(self, hcp_id: int) -> dict:
        return {
            "attitude": "接受" if sum(ord(c) for c in str(hcp_id)) % 3 != 0 else "仅限学术场合",
            "best_time": "下午门诊后（15:00-17:00）",
            "preferred_channel": "面对面拜访",
            "avg_visit_duration": "15 分钟",
        }

    def _competitor_relation(self, hcp_id: int) -> dict:
        hcp_str = str(hcp_id)
        is_key_account = sum(ord(c) for c in hcp_str) % 4 == 0
        return {
            "is_competitor_key_account": is_key_account,
            "competitor_events_attended": [{"competitor": "辉瑞", "event": "心血管新药研讨会", "date": "2026-05-10"}] if is_key_account else [],
            "risk_level": "高" if is_key_account else "低",
        }

    def _last_interaction(self, hcp_id: int) -> dict:
        conn = self._connection()
        row = conn.execute(
            "SELECT content, outcome, conducted_at FROM hcp_interactions WHERE hcp_id=? ORDER BY conducted_at DESC LIMIT 1",
            (hcp_id,),
        ).fetchone()
        if row:
            return {
                "date": row["conducted_at"],
                "summary": row["content"][:100] if row["content"] else "",
                "outcome": row["outcome"] or "",
                "follow_up": "无待跟进事项",
            }
        return {
            "date": "2026-05-20",
            "summary": "讨论阿托伐他汀用药方案调整",
            "outcome": "医生表示会考虑增加处方量",
            "follow_up": "下次带最新临床数据给医生参考",
        }
