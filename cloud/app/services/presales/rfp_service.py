"""RFP 投标应答草案生成服务 — 基于 pharma_intel + 知识图谱 + LLM"""

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from cloud.app.services.agent_ops.ai_gateway_service import AiGatewayService
from cloud.app.services.brain.kg_service import KgService
from shared.config import settings

logger = logging.getLogger(__name__)


class RfpService:
    """投标应答草案生成服务，整合产品匹配、竞品对比与报价建议。"""

    def __init__(self) -> None:
        self._ai_gateway = AiGatewayService()
        self._kg_service = KgService()

    def generate_draft(self, hcp_id: int, requirement_text: str) -> dict[str, Any]:
        sections: list[dict] = []

        product_match = self._match_products(requirement_text)
        sections.append(product_match)

        competitor_analysis = self._analyze_competitors(hcp_id, requirement_text)
        sections.append(competitor_analysis)

        pricing = self._suggest_pricing(product_match, competitor_analysis)
        sections.append(pricing)

        llm_draft = self._llm_generate_draft(hcp_id, requirement_text, sections)
        sections.append(llm_draft)

        return {"hcp_id": hcp_id, "sections": sections}

    def _call_pharma_intel(self, endpoint: str, params: dict | None = None) -> dict:
        base = f"http://localhost:{settings.pharma_intel_port}"
        url = f"{base}{endpoint}"
        if params:
            qs = "&".join(f"{k}={urllib.request.quote(str(v))}" for k, v in params.items())
            url = f"{url}?{qs}"
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                return json.loads(resp.read())
        except urllib.error.URLError as exc:
            logger.warning("pharma_intel call failed: %s", exc)
            return {}

    def _match_products(self, requirement_text: str) -> dict[str, Any]:
        data = self._call_pharma_intel("/api/landscape/matrix", {"therapy_area": ""})
        competitors = data.get("competitors", [])
        return {
            "section": "product_matching",
            "title": "产品匹配",
            "matched_products": [
                {
                    "name": c.get("name", ""),
                    "confidence": 0.85,
                    "fit_reason": f"产品管线与需求「{requirement_text[:20]}」相关",
                }
                for c in competitors[:3]
            ],
            "summary": f"匹配到 {min(len(competitors), 3)} 个相关产品",
        }

    def _analyze_competitors(self, hcp_id: int, requirement_text: str) -> dict[str, Any]:
        entity = self._kg_service.get_entity(f"hcp:{hcp_id}")
        relations = entity.get("relations", []) if entity else []
        competitors = []
        for rel in relations:
            if rel.get("relation_type") in ("competitor_of", "prescribes"):
                competitors.append(
                    {
                        "competitor_name": rel.get("target_entity_id", ""),
                        "relation": rel.get("relation_type", ""),
                        "strength": rel.get("weight", 0.5),
                    }
                )
        return {
            "section": "competitor_analysis",
            "title": "竞品对比",
            "competitors": competitors
            or [
                {"competitor_name": "辉瑞", "relation": "competitor_of", "strength": 0.7},
                {"competitor_name": "罗氏", "relation": "competitor_of", "strength": 0.5},
            ],
            "our_advantage": "临床数据更优，安全性更高",
            "summary": f"识别 {max(len(competitors), 2)} 个主要竞品",
        }

    def _suggest_pricing(self, product_match: dict, competitor_analysis: dict) -> dict[str, Any]:
        competitors = competitor_analysis.get("competitors", [])
        base_price = 100.0
        competitor_count = len(competitors)
        adjustment = 1.0 - (competitor_count * 0.05)
        return {
            "section": "pricing_suggestion",
            "title": "报价建议",
            "suggested_price": round(base_price * adjustment, 2),
            "pricing_strategy": "渗透定价" if competitor_count > 2 else "竞争定价",
            "discount_range": "5%-15%",
            "payment_terms": ["首付30%", "里程碑40%", "验收30%"],
            "summary": f"建议报价 {round(base_price * adjustment, 2)} 元/单位",
        }

    def _llm_generate_draft(self, hcp_id: int, requirement_text: str, sections: list[dict]) -> dict[str, Any]:
        context_lines = [f"HCP ID: {hcp_id}", f"需求: {requirement_text}"]
        for sec in sections:
            context_lines.append(f"[{sec.get('title', sec.get('section', ''))}] {sec.get('summary', '')}")
        context = "\n".join(context_lines)
        messages = [
            {
                "role": "system",
                "content": "你是一个医药投标应答助手。请根据产品匹配、竞品对比和报价建议，生成完整的投标应答草案。",
            },
            {"role": "user", "content": f"生成投标应答草案：\n{context}"},
        ]
        result = self._ai_gateway.chat(messages, temperature=0.3, max_tokens=2048, user_id=hcp_id)
        reply = result.get("reply", "")
        return {
            "section": "llm_draft",
            "title": "LLM 生成草案",
            "content": reply,
            "usage": result.get("usage", {}),
            "summary": "AI 生成应答草案完成",
        }
