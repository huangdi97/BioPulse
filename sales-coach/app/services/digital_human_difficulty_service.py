"""数字人难度服务模块，根据会话表现动态调整训练难度。"""

from fastapi import HTTPException
from starlette import status

from shared.base_service import BaseService


class DigitalHumanDifficultyService(BaseService):
    """DigitalHumanDifficulty 服务类。"""

    def adjust_difficulty(self, session_id: int) -> dict:
        """调整难度。

        Args:
            session_id: 描述

        Returns:
            描述
        """
        row = self.db.execute(
            "SELECT s.*, c.difficulty AS current_level FROM digital_human_sessions s JOIN coach_scenario c ON s.scenario_id = c.id WHERE s.id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")

        current_level = row["current_level"]
        message_count = row["message_count"]
        violations = row["compliance_violations"]
        score = row["overall_score"] or 0

        messages = self.db.execute(
            "SELECT COUNT(*) AS cnt FROM digital_human_messages WHERE session_id = ? AND sender = 'user'",
            (session_id,),
        ).fetchone()
        user_rounds = messages["cnt"]

        difficulty_order = ["beginner", "medium", "advanced"]
        level_map = {lvl: i for i, lvl in enumerate(difficulty_order)}

        reasons = []
        current_idx = level_map.get(current_level, 1)
        adjusted_idx = current_idx

        if message_count < 3:
            adjusted_idx = max(adjusted_idx - 1, 0)
            reasons.append("message_count below 3")
        if violations > 2:
            adjusted_idx = max(adjusted_idx - 1, 0)
            reasons.append("compliance violations exceed 2")
        if user_rounds > 8 and score > 80:
            adjusted_idx = min(adjusted_idx + 1, len(difficulty_order) - 1)
            reasons.append("over 8 rounds with score above 80")

        adjusted_level = difficulty_order[adjusted_idx]

        if adjusted_idx == current_idx:
            reason = "No adjustment needed"
        else:
            direction = "increased" if adjusted_idx > current_idx else "decreased"
            reason = f"Difficulty {direction}: {', '.join(reasons)}"

        return {
            "current_level": current_level,
            "adjusted_level": adjusted_level,
            "reason": reason,
        }
