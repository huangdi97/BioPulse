"""数字人记忆服务模块，管理训练记忆的保存、技能迁移与基准对比。"""

from fastapi import HTTPException
from starlette import status

from shared.base_service import BaseService


class DigitalHumanMemoryService(BaseService):
    """DigitalHumanMemory 服务类。"""

    def save_training_memory(self, session_id: int) -> dict:
        """保存训练记忆。

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

        existing = self.db.execute("SELECT * FROM training_memory WHERE session_id = ?", (session_id,)).fetchone()
        if existing:
            return dict(existing)

        score = row["overall_score"] or 0
        strengths = row["strengths"] or "Not evaluated"
        weaknesses = row["weaknesses"] or "Not evaluated"
        feedback = row["feedback"] or "Not evaluated"

        skills_extracted = strengths

        self.db.execute(
            "INSERT INTO training_memory (session_id, overall_score, feedback, strengths, weaknesses, skills_extracted) VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, score, feedback, strengths, weaknesses, skills_extracted),
        )

        memory = self.db.execute("SELECT * FROM training_memory WHERE session_id = ?", (session_id,)).fetchone()

        return dict(memory)

    def transfer_skills(self, from_session_id: int, to_session_id: int) -> dict:
        """迁移技能。

        Args:
            from_session_id: 描述
            to_session_id: 描述

        Returns:
            描述
        """
        source = self.db.execute("SELECT * FROM training_memory WHERE session_id = ?", (from_session_id,)).fetchone()
        if not source:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Source session has no saved training memory. Save memory first.",
            )

        target = self.db.execute("SELECT * FROM digital_human_sessions WHERE id = ?", (to_session_id,)).fetchone()
        if not target:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Target session not found")

        strengths = source["strengths"]
        weaknesses = source["weaknesses"]
        prev_score = source["overall_score"]

        skill_note = (
            f"[技能迁移] 来自会话 #{from_session_id} 的经验："
            f"之前表现突出的能力：{strengths}。"
            f"待改进方向：{weaknesses}。"
            f"历史评分：{prev_score}。"
            f"请在本次会话中继续巩固优势、针对性改进薄弱项。"
        )

        max_round = self.db.execute(
            "SELECT COALESCE(MAX(round_number), -1) AS mr FROM digital_human_messages WHERE session_id = ?",
            (to_session_id,),
        ).fetchone()
        next_round = max_round["mr"] + 1 if max_round else 0

        self.db.execute(
            "INSERT INTO digital_human_messages (session_id, sender, content, round_number) VALUES (?, ?, ?, ?)",
            (to_session_id, "ai", skill_note, next_round),
        )
        self.db.execute(
            "UPDATE digital_human_sessions SET message_count = message_count + 1 WHERE id = ?",
            (to_session_id,),
        )

        return {
            "from_session_id": from_session_id,
            "to_session_id": to_session_id,
            "skill_note": skill_note,
            "transferred_skills": {
                "strengths": strengths,
                "weaknesses": weaknesses,
                "previous_score": prev_score,
            },
        }

    def get_benchmarks(self) -> dict:
        """获取基准数据。

        Returns:
            描述
        """
        rows = self.db.execute(
            "SELECT s.role, c.difficulty, "
            "COUNT(*) AS session_count, "
            "ROUND(AVG(s.overall_score), 1) AS avg_score, "
            "ROUND(AVG(s.compliance_violations), 1) AS avg_violations, "
            "ROUND(AVG(s.message_count), 1) AS avg_message_count "
            "FROM digital_human_sessions s "
            "JOIN coach_scenario c ON s.scenario_id = c.id "
            "WHERE s.status = 'completed' AND s.overall_score IS NOT NULL "
            "GROUP BY s.role, c.difficulty "
            "ORDER BY s.role, c.difficulty"
        ).fetchall()

        benchmarks: dict[str, dict[str, dict]] = {}
        for r in rows:
            role = r["role"]
            diff = r["difficulty"]
            if role not in benchmarks:
                benchmarks[role] = {}
            benchmarks[role][diff] = {
                "session_count": r["session_count"],
                "avg_score": r["avg_score"],
                "avg_violations": r["avg_violations"],
                "avg_message_count": r["avg_message_count"],
            }
        return benchmarks

    def compare_with_benchmark(self, session_id: int) -> dict:
        """与基准对比。

        Args:
            session_id: 描述

        Returns:
            描述
        """
        row = self.db.execute(
            "SELECT s.*, c.difficulty FROM digital_human_sessions s JOIN coach_scenario c ON s.scenario_id = c.id WHERE s.id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")

        session_data = {
            "session_id": row["id"],
            "role": row["role"],
            "difficulty": row["difficulty"],
            "overall_score": row["overall_score"],
            "compliance_violations": row["compliance_violations"],
            "message_count": row["message_count"],
            "status": row["status"],
        }

        benchmarks = self.get_benchmarks()
        role_bench = benchmarks.get(row["role"], {})
        diff_bench = role_bench.get(row["difficulty"], {})

        comparison = {
            "session": session_data,
            "benchmark": diff_bench,
        }

        if diff_bench:
            score_diff = None
            if row["overall_score"] is not None and diff_bench["avg_score"] is not None:
                score_diff = round(row["overall_score"] - diff_bench["avg_score"], 1)
            comparison["gap"] = {
                "score_vs_benchmark": score_diff,
                "above_average": score_diff > 0 if score_diff is not None else None,
            }
        else:
            comparison["gap"] = None

        return comparison
