"""数字人会话结束评分、画像及列表辅助 mixin。"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from starlette import status


class DHProfileMixin:
    def end_session(self, session_id: int, user_id: int) -> dict:
        row = self.db.execute("SELECT * FROM digital_human_sessions WHERE id = ?", (session_id,)).fetchone()
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
        self._provider.end_session(row.get("external_session_id", ""))
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
            "UPDATE digital_human_sessions SET status = 'completed', overall_score = ?, "
            "feedback = ?, weaknesses = ?, strengths = ?, completed_at = ? WHERE id = ?",
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

    def get_provider_info(self) -> dict:
        return self._provider.get_provider_info()

    def list_sessions(self, user_id: Optional[int] = None, status: Optional[str] = None, limit: int = 20) -> list:
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
        rows = self.db.execute(f"SELECT * FROM digital_human_sessions {where} ORDER BY id DESC LIMIT ?", (*params, limit)).fetchall()
        return [dict(r) for r in rows]
