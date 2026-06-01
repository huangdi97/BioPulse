import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from sales_coach.app.repositories import ModuleRepository, SessionRepository
from sales_coach.app.services.base import BaseService


class SessionService(BaseService):
    def _check_module_exists(self, module_id: int) -> None:
        ModuleRepository(self.db).get_active_or_404(module_id)

    def create(self, module_id: int, body, user_id: int) -> dict:
        self._check_module_exists(module_id)
        repo = SessionRepository(self.db)
        now = datetime.now(timezone.utc).isoformat()
        data = body.model_dump()
        data["module_id"] = module_id
        session_id = repo.create(data, extra={"created_by": user_id, "created_at": now})
        return {"id": session_id}

    def create_digital_human_session(
        self, module_id: int, body, user_id: int,
        session_type: str = "roleplay", scenario_id: int = None,
        role: str = None,
    ) -> dict:
        """Create a digital human coach session with extended fields."""
        self._check_module_exists(module_id)
        repo = SessionRepository(self.db)
        now = datetime.now(timezone.utc).isoformat()
        data = body.model_dump()
        data["module_id"] = module_id
        data["session_type"] = session_type
        data["scenario_id"] = scenario_id
        data["role"] = role
        data["dialogue_log"] = json.dumps([])
        data["compliance_violations"] = 0
        session_id = repo.create(data, extra={"created_by": user_id, "created_at": now})
        return {"id": session_id}

    def update_dialogue_log(self, session_id: int, entry: dict) -> dict:
        """Append a dialogue entry to the session's dialogue log."""
        repo = SessionRepository(self.db)
        row = repo.get_session_or_404(session_id)
        log = json.loads(row["dialogue_log"] or "[]")
        log.append(entry)
        repo.update(session_id, {"dialogue_log": json.dumps(log)})
        return dict(repo.get_session_or_404(session_id))

    def get_dialogue_history(self, session_id: int) -> List[Dict[str, Any]]:
        """Return the full dialogue history for a session."""
        repo = SessionRepository(self.db)
        row = repo.get_session_or_404(session_id)
        return json.loads(row["dialogue_log"] or "[]")

    def update_assessment(self, session_id: int, assessment: dict) -> dict:
        """Update the auto_assessment field for a session."""
        repo = SessionRepository(self.db)
        repo.get_session_or_404(session_id)
        repo.update(session_id, {"auto_assessment": json.dumps(assessment)})
        return dict(repo.get_session_or_404(session_id))

    def update_reflection(self, session_id: int, report: dict) -> dict:
        """Update the reflection_report field for a session."""
        repo = SessionRepository(self.db)
        repo.get_session_or_404(session_id)
        repo.update(session_id, {"reflection_report": json.dumps(report)})
        return dict(repo.get_session_or_404(session_id))

    def list(self, module_id: int, page: int, page_size: int) -> tuple:
        self._check_module_exists(module_id)
        repo = SessionRepository(self.db)
        return repo.paginate_by_module(module_id, page=page, page_size=page_size)

    def get(self, session_id: int) -> dict:
        repo = SessionRepository(self.db)
        return dict(repo.get_session_or_404(session_id))

    def update(self, session_id: int, body) -> dict:
        repo = SessionRepository(self.db)
        repo.get_session_or_404(session_id)
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(repo.get_session_or_404(session_id))
        repo.update(session_id, updates)
        return dict(repo.get_session_or_404(session_id))

    def delete(self, session_id: int) -> None:
        repo = SessionRepository(self.db)
        repo.get_session_or_404(session_id)
        repo.hard_delete(session_id)
