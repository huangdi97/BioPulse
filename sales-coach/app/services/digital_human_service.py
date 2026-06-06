"""数字人服务模块，管理数字人导练会话的创建、对话与评估。"""

import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException
from starlette import status

from sales_coach.app.database import get_db
from sales_coach.app.digital_human import check_compliance, initiate_scenario
from sales_coach.app.services.base import BaseService
from sales_coach.app.services.digital_human_provider import get_provider
from shared.config import settings


class DigitalHumanService(BaseService):
    """DigitalHuman 服务类。"""

    def __init__(self, db=Depends(get_db)):
        super().__init__(db)
        self._provider = get_provider(settings.DIGITAL_HUMAN_PROVIDER)

    def create_session(
        self,
        scenario_id: int,
        module_id: int,
        role: str,
        user_id: int,
    ) -> dict:
        """创建数字人导练会话并初始化首条消息。

        Args:
            scenario_id: 场景ID。
            module_id: 模块ID。
            role: 角色。
            user_id: 创建者用户ID。

        Returns:
            包含会话ID、首条消息和场景信息的字典。
        """
        scenario = self.db.execute(
            "SELECT * FROM coach_scenario WHERE id = ? AND is_active = 1",
            (scenario_id,),
        ).fetchone()
        if not scenario:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Scenario not found")

        now = datetime.now(timezone.utc).isoformat()
        ext_session_id = self._provider.create_session(dict(scenario), user_id)
        cur = self.db.execute(
            "INSERT INTO digital_human_sessions "
            "(scenario_id, module_id, role, created_by, created_at, external_session_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (scenario_id, module_id, role, user_id, now, ext_session_id),
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
        """向数字人会话发送消息并获取AI回复。

        Args:
            session_id: 会话ID。
            content: 用户消息内容。
            ai_gateway_url: AI网关地址。
            user_id: 用户ID。

        Returns:
            包含AI回复、合规检测结果和当前轮次的字典。
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

        msg = {"content": content, "role": row["role"], "ai_gateway_url": ai_gateway_url}
        ext_id = row.get("external_session_id", "")
        provider_result = self._provider.send_message(ext_id, msg, context)

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
        """获取数字人会话详情及消息历史。

        Args:
            session_id: 会话ID。

        Returns:
            包含会话信息和消息列表的字典。
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
        """结束数字人会话，计算评分并生成反馈。

        Args:
            session_id: 会话ID。
            user_id: 操作用户ID。

        Returns:
            包含总评分、反馈、优势弱项等的字典。
        """
        row = self.db.execute(
            "SELECT * FROM digital_human_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
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

    def get_provider_info(self) -> dict:
        """获取当前数字人供应商信息。

        Returns:
            供应商名称、版本、能力及连接状态的字典。
        """
        return self._provider.get_provider_info()

    def list_sessions(
        self,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> list:
        """查询数字人会话列表。

        Args:
            user_id: 按用户ID筛选。
            status: 按状态筛选。
            limit: 返回条数上限。

        Returns:
            会话记录列表。
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
