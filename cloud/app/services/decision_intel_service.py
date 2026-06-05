import json
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any, Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.services.base import BaseService
from cloud.app.services.decision_logger import DecisionLogger
from cloud.app.services.intel_analyzer import IntelAnalyzer


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


class DecisionIntelService(BaseService):
    def __init__(self, db=None):
        super().__init__(db)
        self._logger = DecisionLogger(db)
        self._analyzer = IntelAnalyzer(db)

    def create_case(
        self,
        name: str,
        pipeline_run_id: Optional[int],
        description: str,
        outcome: str,
        outcome_score: float,
        context: dict,
        tags: list,
        uid: int,
    ) -> dict:
        return self._logger.create_case(name, pipeline_run_id, description, outcome, outcome_score, context, tags, uid)

    def list_cases(
        self,
        outcome_score_min: Optional[float] = None,
        outcome_score_max: Optional[float] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        return self._logger.list_cases(outcome_score_min, outcome_score_max, tag, search, page, page_size)

    def get_case(self, case_id: int) -> dict:
        return self._logger.get_case(case_id)

    def update_case(
        self,
        case_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        outcome: Optional[str] = None,
        outcome_score: Optional[float] = None,
        context: Optional[dict] = None,
        tags: Optional[list] = None,
    ) -> dict:
        return self._logger.update_case(case_id, name, description, outcome, outcome_score, context, tags)

    def delete_case(self, case_id: int) -> None:
        return self._logger.delete_case(case_id)

    def analyze_case(self, case_id: int, custom_question: str, auth_header: str) -> dict:
        return self._analyzer.analyze_case(case_id, custom_question, auth_header)

    def list_analyses(self, case_id: int) -> list:
        return self._analyzer.list_analyses(case_id)

    def get_analysis(self, analysis_id: int) -> dict:
        return self._analyzer.get_analysis(analysis_id)

    def reflect(self, filter_tags: list, max_cases: int, auth_header: str) -> dict:
        return self._analyzer.reflect(filter_tags, max_cases, auth_header)

    def list_insights(
        self,
        insight_type: Optional[str] = None,
        confidence_min: Optional[float] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        return self._logger.list_insights(insight_type, confidence_min, page, page_size)

    def get_insight(self, insight_id: int) -> dict:
        return self._logger.get_insight(insight_id)

    def update_insight(
        self,
        insight_id: int,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        confidence: Optional[float] = None,
        applicability: Optional[str] = None,
    ) -> dict:
        return self._logger.update_insight(insight_id, title, summary, confidence, applicability)

    def dashboard(self) -> dict:
        return self._logger.dashboard()
