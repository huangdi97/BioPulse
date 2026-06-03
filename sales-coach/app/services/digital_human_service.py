import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from starlette import status

from sales_coach.app.digital_human import (
    check_compliance,
    initiate_scenario,
    simulate_dialogue,
)
from sales_coach.app.services.base import BaseService


class DigitalHumanService(BaseService):
    """DigitalHuman 服务类。"""

    def create_session(
        self,
        scenario_id: int,
        module_id: int,
        role: str,
        user_id: int,
    ) -> dict:
        """创建会话。

        Args:
            scenario_id: 描述
            module_id: 描述
            role: 描述
            user_id: 描述

        Returns:
            描述
        """
        scenario = self.db.execute(
            "SELECT * FROM coach_scenario WHERE id = ? AND is_active = 1",
            (scenario_id,),
        ).fetchone()
        if not scenario:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Scenario not found")

        now = datetime.now(timezone.utc).isoformat()
        cur = self.db.execute(
            "INSERT INTO digital_human_sessions (scenario_id, module_id, role, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
            (scenario_id, module_id, role, user_id, now),
        )
        session_id = cur.lastrowid

        init = initiate_scenario(dict(scenario), user_id)
        self.db.execute(
            "INSERT INTO digital_human_messages (session_id, sender, content, round_number) VALUES (?, ?, ?, ?)",
            (session_id, "ai", init["first_message"], 0),
        )
        self.db.execute(
            "UPDATE digital_human_sessions SET message_count = 1 WHERE id = ?",
            (session_id,),
        )

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

    def send_message(
        self,
        session_id: int,
        content: str,
        ai_gateway_url: str,
        user_id: int,
    ) -> dict:
        """发送消息。

        Args:
            session_id: 描述
            content: 描述
            ai_gateway_url: 描述
            user_id: 描述

        Returns:
            描述
        """
        row = self.db.execute(
            "SELECT * FROM digital_human_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
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

        ai_result = simulate_dialogue(row["role"], context, content, ai_gateway_url)

        round_number = len(history)
        self.db.execute(
            "INSERT INTO digital_human_messages "
            "(session_id, sender, content, round_number, compliance_passed, compliance_detail) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                session_id,
                "user",
                content,
                round_number,
                1 if compliance_result["passed"] else 0,
                json.dumps(compliance_result, ensure_ascii=False),
            ),
        )
        self.db.execute(
            "INSERT INTO digital_human_messages (session_id, sender, content, round_number) VALUES (?, ?, ?, ?)",
            (session_id, "ai", ai_result["reply"], round_number + 1),
        )

        violation_inc = 0 if compliance_result["passed"] else len(compliance_result["violations"])
        self.db.execute(
            "UPDATE digital_human_sessions SET message_count = message_count + 2, compliance_violations = compliance_violations + ? WHERE id = ?",
            (violation_inc, session_id),
        )

        return {
            "reply": ai_result["reply"],
            "compliance": compliance_result,
            "round": ai_result["round"],
            "role": row["role"],
        }

    def get_session(self, session_id: int) -> dict:
        """获取会话。

        Args:
            session_id: 描述

        Returns:
            描述
        """
        row = self.db.execute(
            "SELECT * FROM digital_human_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")

        messages = self.db.execute(
            "SELECT * FROM digital_human_messages WHERE session_id = ? ORDER BY round_number ASC",
            (session_id,),
        ).fetchall()

        return {
            "session": dict(row),
            "messages": [dict(m) for m in messages],
        }

    def end_session(self, session_id: int, user_id: int) -> dict:
        """结束会话。

        Args:
            session_id: 描述
            user_id: 描述

        Returns:
            描述
        """
        row = self.db.execute(
            "SELECT * FROM digital_human_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")

        messages = self.db.execute(
            "SELECT * FROM digital_human_messages WHERE session_id = ? AND sender = 'user' ORDER BY round_number ASC",
            (session_id,),
        ).fetchall()

        message_count = row["message_count"]
        violations = row["compliance_violations"]

        user_rounds = len(messages)
        short_replies = sum(1 for m in messages if len(m["content"].strip()) < 5)

        score = 0
        if message_count >= 5:
            score += 60
        else:
            score += 40

        if violations == 0:
            score += 20
        elif violations <= 2:
            score += 10
        else:
            score += 0

        if short_replies == 0:
            score += 10

        if user_rounds > 3:
            score += 10

        overall_score = min(score, 100)

        if overall_score >= 90:
            feedback = "Excellent performance! You demonstrated strong communication skills and compliance awareness."
            strengths = "Clear communication, strong compliance, effective dialogue management"
            weaknesses = "Continue to refine your approach for even better results"
        elif overall_score >= 75:
            feedback = "Good performance! You showed solid skills with some areas for improvement."
            strengths = "Good engagement, mostly compliant communication"
            weaknesses = "Work on reducing compliance violations and maintaining longer conversations"
        elif overall_score >= 60:
            feedback = "Adequate performance. Focus on improving compliance and deepening your responses."
            strengths = "Basic dialogue maintained"
            weaknesses = "Compliance violations need attention, responses could be more detailed"
        else:
            feedback = "Needs improvement. Practice more sessions to build your skills."
            strengths = "Session initiated successfully"
            weaknesses = "Focus on compliance, response quality, and conversation depth"

        now = datetime.now(timezone.utc).isoformat()
        self.db.execute(
            "UPDATE digital_human_sessions SET "
            "status = 'completed', overall_score = ?, feedback = ?, "
            "weaknesses = ?, strengths = ?, completed_at = ? "
            "WHERE id = ?",
            (overall_score, feedback, weaknesses, strengths, now, session_id),
        )

        return {
            "session_id": session_id,
            "overall_score": overall_score,
            "feedback": feedback,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "message_count": message_count,
            "compliance_violations": violations,
            "user_rounds": user_rounds,
        }

    def list_sessions(
        self,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> list:
        """获取会话列表。

        Args:
            user_id: 描述
            status: 描述
            limit: 描述

        Returns:
            描述
        """
        conditions = []
        params = []

        if user_id is not None:
            conditions.append("created_by = ?")
            params.append(user_id)
        if status:
            conditions.append("status = ?")
            params.append(status)

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        rows = self.db.execute(
            f"SELECT * FROM digital_human_sessions {where} ORDER BY id DESC LIMIT ?",
            (*params, limit),
        ).fetchall()

        return [dict(r) for r in rows]
