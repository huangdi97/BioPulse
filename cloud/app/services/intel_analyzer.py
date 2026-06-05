import json
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    CausalAnalysesRepository,
    CrossCaseInsightsRepository,
    DecisionCasesRepository,
)
from cloud.app.services.base import BaseService


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _parse_json(raw: str, default: Any = None) -> Any:
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else raw


def _call_ai(messages: list[dict], auth_header: str) -> dict:
    payload = {"messages": messages, "temperature": 0.7, "max_tokens": 2048}
    req = urllib.request.Request(
        "http://localhost:8000/ai/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": auth_header},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as rp:
        return json.loads(rp.read().decode("utf-8")).get("data", {})


def _e404(name: str = "Resource"):
    raise HTTPException(status.HTTP_404_NOT_FOUND, f"{name} not found")


class IntelAnalyzer(BaseService):
    def analyze_case(self, case_id: int, custom_question: str, auth_header: str) -> dict:
        row = DecisionCasesRepository(self.db).get_active_by_id(case_id)
        if not row:
            _e404("Case")
        ctx = _parse_json(row["context"], {})
        desc = f"案例名称: {row['name']}\n描述: {row['description']}\n结果: {row['outcome']}\n评分: {row['outcome_score']}"
        if ctx:
            desc += f"\n上下文: {json.dumps(ctx, ensure_ascii=False)}"
        if custom_question:
            desc += f"\n\n请额外回答以下问题: {custom_question}"
        sys_prompt = (
            "你是一名因果推断分析师。分析以下决策案例，识别因果链。以JSON格式输出: "
            "{key_drivers:[{factor,impact,direction}],causal_chain:[{cause,effect,strength}],"
            "attribution_scores:{factor:score},recommendations:[string]}"
        )
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": desc},
        ]
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
        analysis_id = analysis_repo.create(
            {
                "case_id": case_id,
                "summary": summary,
                "key_drivers": json.dumps(kd, ensure_ascii=False),
                "causal_chain": json.dumps(cc, ensure_ascii=False),
                "attribution_scores": json.dumps(at, ensure_ascii=False),
                "recommendations": json.dumps(recs, ensure_ascii=False),
                "ai_response_raw": reply,
                "tokens_used": tokens,
            }
        )
        return {
            "analysis_id": analysis_id,
            "summary": summary,
            "key_drivers": kd,
            "causal_chain": cc,
            "attribution_scores": at,
            "recommendations": recs,
        }

    def list_analyses(self, case_id: int) -> list:
        return CausalAnalysesRepository(self.db).list_by_case_id(case_id)

    def get_analysis(self, analysis_id: int) -> dict:
        row = CausalAnalysesRepository(self.db).get_by_id(analysis_id)
        if not row:
            _e404("Analysis")
        return row

    def reflect(self, filter_tags: list, max_cases: int, auth_header: str) -> dict:
        case_repo = DecisionCasesRepository(self.db)
        limit = min(max_cases, 5)
        succ_rows = case_repo.list_success_cases(limit=limit, filter_tags=filter_tags or None)
        fail_rows = case_repo.list_fail_cases(limit=limit, filter_tags=filter_tags or None)

        def _fmt(rows, label):
            return "\n".join(f"{label}: {r['name']} (评分:{r['outcome_score']}) - {r['description']}" for r in rows) or "无"

        sys_prompt = (
            "你是一名销售策略分析导师。对比以下成功和失败的决策案例，识别可复用的模式和应避免的陷阱。"
            "以JSON格式输出:{patterns:[{title,summary,evidence_case_ids:[],confidence}],"
            "pitfalls:[{title,summary,evidence_case_ids:[],confidence}],"
            "best_practices:[{title,summary,applicability}]}"
        )
        messages = [
            {"role": "system", "content": sys_prompt},
            {
                "role": "user",
                "content": f"成功案例:\n{_fmt(succ_rows, '成功案例')}\n\n失败案例:\n{_fmt(fail_rows, '失败案例')}",
            },
        ]
        data = _call_ai(messages, auth_header)
        reply = data.get("reply", "")
        parsed = _parse_json(reply, {})
        n = _now()
        count = 0
        insight_repo = CrossCaseInsightsRepository(self.db)
        if isinstance(parsed, dict):
            for itype, key in [
                ("pattern", "patterns"),
                ("pitfall", "pitfalls"),
                ("best_practice", "best_practices"),
            ]:
                for item in parsed.get(key) if isinstance(parsed.get(key), list) else []:
                    if not isinstance(item, dict):
                        continue
                    insight_repo.create(
                        {
                            "title": item.get("title", ""),
                            "insight_type": itype,
                            "summary": item.get("summary", ""),
                            "detail": json.dumps(item, ensure_ascii=False),
                            "evidence": json.dumps(item.get("evidence_case_ids", []), ensure_ascii=False),
                            "confidence": item.get("confidence", 0.5),
                            "applicability": item.get("applicability", "general"),
                            "source_run_ids": "[]",
                            "created_at": n,
                            "updated_at": n,
                        }
                    )
                    count += 1
        return {"new_insights_count": count}
