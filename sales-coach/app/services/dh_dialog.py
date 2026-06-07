"""数字人对话逻辑 mixin：创建、发送消息、获取会话。"""

import json
from datetime import datetime, timezone

from fastapi import HTTPException
from starlette import status

from sales_coach.app.digital_human import check_compliance, initiate_scenario


class DHDialogMixin:
    def create_session(self, scenario_id: int, module_id: int, role: str, user_id: int) -> dict:
        scenario = self.db.execute("SELECT * FROM coach_scenario WHERE id = ? AND is_active = 1", (scenario_id,)).fetchone()
        if not scenario:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Scenario not found")
        now = datetime.now(timezone.utc).isoformat()
        ext_session_id = self._provider.create_session(dict(scenario), user_id)
        cur = self.db.execute(
            "INSERT INTO digital_human_sessions (scenario_id, module_id, role, "
            "created_by, created_at, external_session_id) VALUES (?, ?, ?, ?, ?, ?)",
            (scenario_id, module_id, role, user_id, now, ext_session_id),
        )
        session_id = cur.lastrowid
        init = initiate_scenario(dict(scenario), user_id)
        self.db.execute(
            "INSERT INTO digital_human_messages (session_id, sender, content, round_number) VALUES (?, ?, ?, ?)",
            (session_id, "ai", init["first_message"], 0),
        )
        self.db.execute("UPDATE digital_human_sessions SET message_count = 1 WHERE id = ?", (session_id,))
        return {
            "session_id": session_id,
            "first_message": init["first_message"],
            "role": role,
            "scenario_info": {
                "title": scenario["title"],
                "difficulty": scenario["difficulty"],
                "category": scenario["category"],
                "goal": scenario["goal"],
            },
        }

    def send_message(self, session_id: int, content: str, ai_gateway_url: str, user_id: int) -> dict:
        row = self.db.execute("SELECT * FROM digital_human_sessions WHERE id = ?", (session_id,)).fetchone()
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
        if row["status"] != "in_progress":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Session is not in progress")
        compliance_result = check_compliance(content)
        history = self.db.execute(
            "SELECT sender, content FROM digital_human_messages WHERE session_id = ? ORDER BY round_number ASC LIMIT 20",
            (session_id,),
        ).fetchall()
        context = [{"role": m["sender"], "content": m["content"]} for m in history]
        msg = {"content": content, "role": row["role"], "ai_gateway_url": ai_gateway_url}
        ext_id = row.get("external_session_id", "")
        provider_result = self._provider.send_message(ext_id, msg, context)
        round_number = len(history)
        self.db.execute(
            "INSERT INTO digital_human_messages (session_id, sender, content, round_number, "
            "compliance_passed, compliance_detail) VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, "user", content, round_number, 1 if compliance_result["passed"] else 0, json.dumps(compliance_result, ensure_ascii=False)),
        )
        self.db.execute(
            "INSERT INTO digital_human_messages (session_id, sender, content, round_number) VALUES (?, ?, ?, ?)",
            (session_id, "ai", provider_result["reply"], round_number + 1),
        )
        violation_inc = 0 if compliance_result["passed"] else len(compliance_result["violations"])
        self.db.execute(
            "UPDATE digital_human_sessions SET message_count = message_count + 2, compliance_violations = compliance_violations + ? WHERE id = ?",
            (violation_inc, session_id),
        )
        return {
            "reply": provider_result["reply"],
            "compliance": compliance_result,
            "round": round_number // 2 + 1,
            "role": row["role"],
        }

    def get_session(self, session_id: int) -> dict:
        row = self.db.execute("SELECT * FROM digital_human_sessions WHERE id = ?", (session_id,)).fetchone()
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
        messages = self.db.execute("SELECT * FROM digital_human_messages WHERE session_id = ? ORDER BY round_number ASC", (session_id,)).fetchall()
        return {"session": dict(row), "messages": [dict(m) for m in messages]}
