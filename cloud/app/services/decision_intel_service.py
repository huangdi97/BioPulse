import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import Any, Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    CausalAnalysesRepository,
    CrossCaseInsightsRepository,
    DecisionCasesRepository,
    PipelineRunsRepository,
    PipelineStepRunsRepository,
)
from cloud.app.services.base import BaseService
from shared.base import validate_columns
from shared.columns import TABLE_DECISION_CASES_COLS, TABLE_CROSS_CASE_INSIGHTS_COLS


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _parse_json(raw: str, default: Any = None) -> Any:
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else raw


def _call_ai(messages: list[dict], auth_header: str) -> dict:
    payload = {"messages": messages, "temperature": 0.7, "max_tokens": 2048}
    req = urllib.request.Request("http://localhost:8000/ai/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": auth_header}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as rp:
        return json.loads(rp.read().decode("utf-8")).get("data", {})


def _e404(name: str = "Resource"):
    raise HTTPException(status.HTTP_404_NOT_FOUND, f"{name} not found")


class DecisionIntelService(BaseService):
    def create_case(self, name: str, pipeline_run_id: Optional[int],
                    description: str, outcome: str,
                    outcome_score: float, context: dict,
                    tags: list, uid: int) -> dict:
        ctx = context
        if pipeline_run_id:
            run_repo = PipelineRunsRepository(self.db)
            run = run_repo.get_by_id(pipeline_run_id)
            if run:
                step_repo = PipelineStepRunsRepository(self.db)
                steps = step_repo.list_all(
                    conditions=["run_id=?"], params=[pipeline_run_id],
                    order_by="step_order")
                ctx = {**ctx, "pipeline_run": run, "step_runs": steps}
        case_repo = DecisionCasesRepository(self.db)
        case_id = case_repo.create({
            "name": name, "pipeline_run_id": pipeline_run_id,
            "description": description, "outcome": outcome,
            "outcome_score": outcome_score,
            "context": json.dumps(ctx, ensure_ascii=False),
            "tags": json.dumps(tags, ensure_ascii=False),
            "created_by": uid, "created_at": _now(), "updated_at": _now(),
        })
        return case_repo.get_by_id(case_id)

    def list_cases(self, outcome_score_min: Optional[float] = None,
                   outcome_score_max: Optional[float] = None,
                   tag: Optional[str] = None,
                   search: Optional[str] = None,
                   page: int = 1, page_size: int = 20) -> dict:
        case_repo = DecisionCasesRepository(self.db)
        total, total_pages, items = case_repo.list_filtered(
            outcome_score_min=outcome_score_min, outcome_score_max=outcome_score_max,
            tag=tag, search=search, page=page, page_size=page_size)
        return {"items": items, "total": total, "page": page,
                "page_size": page_size, "total_pages": total_pages}

    def get_case(self, case_id: int) -> dict:
        row = DecisionCasesRepository(self.db).get_active_by_id(case_id)
        if not row:
            _e404("Case")
        return row

    def update_case(self, case_id: int, name: Optional[str] = None,
                    description: Optional[str] = None,
                    outcome: Optional[str] = None,
                    outcome_score: Optional[float] = None,
                    context: Optional[dict] = None,
                    tags: Optional[list] = None) -> dict:
        case_repo = DecisionCasesRepository(self.db)
        row = case_repo.get_active_by_id(case_id)
        if not row:
            _e404("Case")
        updates = {}
        for f in ("name", "description", "outcome", "outcome_score"):
            v = locals().get(f)
            if v is not None:
                updates[f] = v
        if context is not None:
            updates["context"] = json.dumps(context, ensure_ascii=False)
        if tags is not None:
            updates["tags"] = json.dumps(tags, ensure_ascii=False)
        if updates:
            updates["updated_at"] = _now()
            validate_columns(updates, 'decision_cases', TABLE_DECISION_CASES_COLS)
            case_repo.update(case_id, updates)
        return case_repo.get_by_id(case_id)

    def delete_case(self, case_id: int) -> None:
        case_repo = DecisionCasesRepository(self.db)
        row = case_repo.get_active_by_id(case_id)
        if not row:
            _e404("Case")
        case_repo.soft_delete_with_causal(case_id)

    def analyze_case(self, case_id: int, custom_question: str,
                     auth_header: str) -> dict:
        row = DecisionCasesRepository(self.db).get_active_by_id(case_id)
        if not row:
            _e404("Case")
        ctx = _parse_json(row["context"], {})
        desc = (f"案例名称: {row['name']}\n描述: {row['description']}\n"
                f"结果: {row['outcome']}\n评分: {row['outcome_score']}")
        if ctx:
            desc += f"\n上下文: {json.dumps(ctx, ensure_ascii=False)}"
        if custom_question:
            desc += f"\n\n请额外回答以下问题: {custom_question}"
        sys_prompt = ("你是一名因果推断分析师。分析以下决策案例，识别因果链。以JSON格式输出: "
                      "{key_drivers:[{factor,impact,direction}],causal_chain:[{cause,effect,strength}],"
                      "attribution_scores:{factor:score},recommendations:[string]}")
        messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": desc}]
        data = _call_ai(messages, auth_header)
        reply = data.get("reply", "")
        usage = data.get("usage", {}) or {}
        tokens = usage.get("total_tokens", 0)
        parsed = _parse_json(reply, {})
        if isinstance(parsed, dict):
            summary = parsed.get("summary", reply[:200])
            kd = parsed.get("key_drivers", [])
            cc = parsed.get("causal_chain", [])
            at = parsed.get("attribution_scores", {})
            recs = parsed.get("recommendations", [])
        else:
            summary = reply[:200]
            kd, cc, at, recs = [], [], {}, []
        analysis_repo = CausalAnalysesRepository(self.db)
        analysis_id = analysis_repo.create({
            "case_id": case_id, "summary": summary,
            "key_drivers": json.dumps(kd, ensure_ascii=False),
            "causal_chain": json.dumps(cc, ensure_ascii=False),
            "attribution_scores": json.dumps(at, ensure_ascii=False),
            "recommendations": json.dumps(recs, ensure_ascii=False),
            "ai_response_raw": reply, "tokens_used": tokens,
        })
        return {"analysis_id": analysis_id, "summary": summary,
                "key_drivers": kd, "causal_chain": cc,
                "attribution_scores": at, "recommendations": recs}

    def list_analyses(self, case_id: int) -> list:
        return CausalAnalysesRepository(self.db).list_by_case_id(case_id)

    def get_analysis(self, analysis_id: int) -> dict:
        row = CausalAnalysesRepository(self.db).get_by_id(analysis_id)
        if not row:
            _e404("Analysis")
        return row

    def reflect(self, filter_tags: list, max_cases: int,
                auth_header: str) -> dict:
        case_repo = DecisionCasesRepository(self.db)
        limit = min(max_cases, 5)
        succ_rows = case_repo.list_success_cases(limit=limit, filter_tags=filter_tags or None)
        fail_rows = case_repo.list_fail_cases(limit=limit, filter_tags=filter_tags or None)

        def _fmt(rows, label):
            return "\n".join(
                f"{label}: {r['name']} (评分:{r['outcome_score']}) - {r['description']}" for r in rows) or "无"

        sys_prompt = ("你是一名销售策略分析导师。对比以下成功和失败的决策案例，识别可复用的模式和应避免的陷阱。"
                      "以JSON格式输出:{patterns:[{title,summary,evidence_case_ids:[],confidence}],"
                      "pitfalls:[{title,summary,evidence_case_ids:[],confidence}],"
                      "best_practices:[{title,summary,applicability}]}")
        messages = [{"role": "system", "content": sys_prompt},
                    {"role": "user", "content": f"成功案例:\n{_fmt(succ_rows,'成功案例')}\n\n失败案例:\n{_fmt(fail_rows,'失败案例')}"}]
        data = _call_ai(messages, auth_header)
        reply = data.get("reply", "")
        parsed = _parse_json(reply, {})
        n = _now()
        count = 0
        insight_repo = CrossCaseInsightsRepository(self.db)
        if isinstance(parsed, dict):
            for itype, key in [("pattern", "patterns"), ("pitfall", "pitfalls"), ("best_practice", "best_practices")]:
                for item in (parsed.get(key) if isinstance(parsed.get(key), list) else []):
                    if not isinstance(item, dict):
                        continue
                    insight_repo.create({
                        "title": item.get("title", ""), "insight_type": itype,
                        "summary": item.get("summary", ""),
                        "detail": json.dumps(item, ensure_ascii=False),
                        "evidence": json.dumps(item.get("evidence_case_ids", []), ensure_ascii=False),
                        "confidence": item.get("confidence", 0.5),
                        "applicability": item.get("applicability", "general"),
                        "source_run_ids": "[]", "created_at": n, "updated_at": n,
                    })
                    count += 1
        return {"new_insights_count": count}

    def list_insights(self, insight_type: Optional[str] = None,
                      confidence_min: Optional[float] = None,
                      page: int = 1, page_size: int = 20) -> dict:
        total, total_pages, items = CrossCaseInsightsRepository(self.db).list_filtered(
            insight_type=insight_type, confidence_min=confidence_min,
            page=page, page_size=page_size)
        return {"items": items, "total": total, "page": page,
                "page_size": page_size, "total_pages": total_pages}

    def get_insight(self, insight_id: int) -> dict:
        row = CrossCaseInsightsRepository(self.db).get_active_by_id(insight_id)
        if not row:
            _e404("Insight")
        return row

    def update_insight(self, insight_id: int,
                       title: Optional[str] = None,
                       summary: Optional[str] = None,
                       confidence: Optional[float] = None,
                       applicability: Optional[str] = None) -> dict:
        repo = CrossCaseInsightsRepository(self.db)
        row = repo.get_active_by_id(insight_id)
        if not row:
            _e404("Insight")
        updates = {}
        for f in ("title", "summary", "confidence", "applicability"):
            v = locals().get(f)
            if v is not None:
                updates[f] = v
        if updates:
            updates["updated_at"] = _now()
            validate_columns(updates, 'cross_case_insights', TABLE_CROSS_CASE_INSIGHTS_COLS)
            repo.update(insight_id, updates)
        return repo.get_by_id(insight_id)

    def dashboard(self) -> dict:
        case_repo = DecisionCasesRepository(self.db)
        analysis_repo = CausalAnalysesRepository(self.db)
        insight_repo = CrossCaseInsightsRepository(self.db)
        total_cases = case_repo.count_active()
        analyzed = analysis_repo.count_distinct_case_ids()
        score_dist = case_repo.score_distribution()
        insight_counts = insight_repo.count_by_type()
        top_insights = insight_repo.top_by_confidence(5)
        return {
            "total_cases": total_cases, "analyzed_cases": analyzed,
            "score_distribution": score_dist,
            "insights_by_type": insight_counts,
            "top_insights": top_insights,
        }
