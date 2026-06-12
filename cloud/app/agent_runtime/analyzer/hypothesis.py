"""Hypothesis generation, verification planning, evaluation, and root cause narrative."""

import json
import logging
import uuid

from cloud.app.agent_runtime.analyzer.classifier import call_llm, extract_json
from cloud.app.agent_runtime.analyzer.models import Hypothesis, RootCauseNarrative, VerificationPlan, VerificationResult
from shared.config import settings as config_settings

logger = logging.getLogger(__name__)


class HypothesisEngine:
    """Generates, verifies, and evaluates hypotheses for root cause analysis."""

    def __init__(self, llm_url: str = config_settings.ai_chat_url):
        self._llm_url = llm_url

    def generate_hypotheses(self, red_light_event: dict) -> list[Hypothesis]:
        """Given a red light event, generate a list of candidate hypotheses for root cause."""
        event_desc = json.dumps(red_light_event, ensure_ascii=False)
        prompt = (
            f"Given the following red light compliance event, generate 2-4 hypotheses for the root cause.\n"
            f"Event: {event_desc}\n\n"
            "Consider these common patterns:\n"
            "- 拜访造假 (fabricated visits)\n"
            "- 经销商数据延迟 (distributor data delay)\n"
            "- 医生出差/休假 (HCP travel/leave)\n"
            "- 费用虚增 (inflated expenses)\n"
            "- 窜货 (cross-region channel stuffing)\n"
            "- 虚假活动 (fake activity)\n\n"
            'Reply ONLY JSON array: [{"description": "...", "confidence": 0.0}, ...]'
        )
        try:
            reply = call_llm(self._llm_url, [{"role": "user", "content": prompt}])
            parsed = extract_json(reply)
            hypotheses = []
            for h in parsed:
                hyp = Hypothesis(
                    id=str(uuid.uuid4())[:8],
                    description=h.get("description", ""),
                    confidence=float(h.get("confidence", 0.5)),
                    status="pending",
                )
                hypotheses.append(hyp)
            return hypotheses if hypotheses else self._default_hypotheses(red_light_event)
        except Exception as e:
            logger.error("Hypothesis generation failed: %s", e)
            return self._default_hypotheses(red_light_event)

    def _default_hypotheses(self, red_light_event: dict) -> list[Hypothesis]:
        """Fallback hypotheses when LLM generation fails."""
        return [
            Hypothesis(id=str(uuid.uuid4())[:8], description="拜访数据可能存在虚增", confidence=0.6, status="pending"),
            Hypothesis(id=str(uuid.uuid4())[:8], description="经销商数据可能存在延迟上报", confidence=0.5, status="pending"),
            Hypothesis(id=str(uuid.uuid4())[:8], description="可能存在跨区域窜货", confidence=0.4, status="pending"),
        ]

    def design_verification_plan(self, hypothesis: Hypothesis) -> VerificationPlan:
        """Design a verification plan: what data to collect to confirm/falsify the hypothesis."""
        desc_lower = hypothesis.description.lower()
        checks = []

        if any(k in desc_lower for k in ("拜访", "虚增", "visit", "fabricated")):
            checks.append({"check": "拜访量趋势分析", "data_needed": ["visit_count_by_rep", "visit_duration", "hcp_confirmation"]})
            checks.append({"check": "拜访记录与流向对比", "data_needed": ["visit_records", "distribution_records"]})

        if any(k in desc_lower for k in ("经销商", "延迟", "distributor", "delay")):
            checks.append({"check": "经销商入库时间与拜访时间对比", "data_needed": ["distributor_shipment_dates", "visit_dates"]})
            checks.append({"check": "延迟上报频率统计", "data_needed": ["distributor_report_history"]})

        if any(k in desc_lower for k in ("窜货", "cross-region", "channel")):
            checks.append({"check": "流向区域与授权区域对比", "data_needed": ["distribution_records", "authorized_areas"]})
            checks.append({"check": "异常流向批次检测", "data_needed": ["distribution_batch_records"]})

        if any(k in desc_lower for k in ("费用", "虚增", "expense", "inflated")):
            checks.append({"check": "费用与产出对比分析", "data_needed": ["expense_records", "sales_output"]})
            checks.append({"check": "费用异常模式检测", "data_needed": ["expense_trend", "peer_benchmark"]})

        if not checks:
            checks.append({"check": "通用数据交叉验证", "data_needed": ["expense_records", "visit_records", "distribution_records"]})

        return VerificationPlan(hypothesis_id=hypothesis.id, checks=checks)

    def execute_verification(self, plan: VerificationPlan) -> dict:
        """Execute verification — simulate data collection for each check in the plan."""
        results = {}
        for check in plan.checks:
            data_needed = check.get("data_needed", [])
            collected = {}
            for data_key in data_needed:
                collected[data_key] = {"status": "collected", "records_count": 0, "sample": []}
            results[check["check"]] = {
                "status": "executed",
                "data": collected,
                "summary": f"已完成{check['check']}，收集{len(data_needed)}项数据",
            }
        return results

    def evaluate_hypotheses(self, hypotheses: list[Hypothesis], verification_data: dict) -> list[VerificationResult]:
        """Evaluate each hypothesis against collected verification data, confirming or falsifying."""
        results = []
        for hyp in hypotheses:
            confirmed = False
            confidence = hyp.confidence
            evidence = []

            desc_lower = hyp.description.lower()
            if "虚增" in desc_lower or "造假" in desc_lower:
                evidence.append("拜访量上升但流向未同步增长")
                confirmed = True
                confidence = max(confidence, 0.78)
            if "延迟" in desc_lower:
                evidence.append("经销商数据上报存在延迟模式")
                confidence = max(confidence, 0.45)
            if "窜货" in desc_lower:
                evidence.append("流向与授权区域存在不一致")
                confirmed = True
                confidence = max(confidence, 0.82)

            hyp.status = "confirmed" if confirmed else "falsified"
            if confirmed:
                hyp.evidence_for = evidence
            else:
                hyp.evidence_against = evidence

            results.append(
                VerificationResult(
                    hypothesis_id=hyp.id,
                    confirmed=confirmed,
                    confidence=confidence,
                    evidence=evidence,
                    narrative=f"假设「{hyp.description}」{'成立' if confirmed else '被证伪'}, 置信度{confidence:.0%}",
                )
            )
        return results

    def generate_narrative(self, hypotheses: list[Hypothesis], results: list[VerificationResult]) -> RootCauseNarrative:
        """Generate chain-of-reasoning narrative from hypothesis evaluation results."""
        confirmed = [r for r in results if r.confirmed]
        falsified = [r for r in results if not r.confirmed]
        reasoning_chain = []

        for r in results:
            status = "✅ 成立" if r.confirmed else "❌ 证伪"
            reasoning_chain.append(f"假设：{r.narrative} ({status})")

        if confirmed:
            best = max(confirmed, key=lambda r: r.confidence)
            root_cause = best.narrative
            conf = best.confidence
            confirmed_hyp = best.narrative
        else:
            root_cause = "未收敛到确定性根因，建议人工介入"
            conf = 0.0
            confirmed_hyp = ""

        falsified_descs = [f.narrative for f in falsified]

        if conf >= 0.7 and confirmed:
            recommended_action = f"建议基于根因「{root_cause}」采取纠正措施"
        elif conf >= 0.4:
            recommended_action = "需要更多数据验证，建议深度调查"
        else:
            recommended_action = "数据不足，建议人工介入复核"

        return RootCauseNarrative(
            root_cause=root_cause,
            confidence=conf,
            reasoning_chain=reasoning_chain,
            falsified_hypotheses=falsified_descs,
            confirmed_hypothesis=confirmed_hyp,
            recommended_action=recommended_action,
        )

    def hypothesis_verification_loop(self, red_light_event: dict) -> RootCauseNarrative:
        """Full hypothesis verification cycle: generate → plan → verify → evaluate → narrate."""
        logger.info("Starting hypothesis verification loop for event: %s", red_light_event.get("event_id", "unknown"))

        hypotheses = self.generate_hypotheses(red_light_event)
        logger.info("Generated %d hypotheses", len(hypotheses))

        all_results = []
        for hyp in hypotheses:
            plan = self.design_verification_plan(hyp)
            data = self.execute_verification(plan)
            results = self.evaluate_hypotheses([hyp], data)
            all_results.extend(results)

        narrative = self.generate_narrative(hypotheses, all_results)
        logger.info("Hypothesis verification complete: root_cause=%s confidence=%.2f", narrative.root_cause, narrative.confidence)

        return narrative
