import json
import urllib.request
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from starlette import status

from cloud.app.database import get_db
from cloud.app.repositories import (
    AgentRolesRepository,
    MdtOpinionsRepository,
    MdtParticipantsRepository,
    MdtSessionsRepository,
)
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/mdt", tags=["MDT会诊"])


class ParticipantDef(BaseModel):
    agent_role_id: int
    role_name: str
    stance: str = "neutral"
    vote_weight: float = 1.0


class SessionCreate(BaseModel):
    title: str
    question: str
    context: str = ""
    participants: list[ParticipantDef] = []


class DebateRequest(BaseModel):
    max_rounds: int = 1


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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


def _parse_json(raw: str, default=None):
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else raw


def _n404(name="Resource"):
    raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"{name} not found")


# --- endpoints ---


@router.post("/sessions", status_code=201)
def create_session(
    body: SessionCreate,
    request: Request,
    current_user=Depends(require_scope("visit")),
    db=Depends(get_db),
):
    """创建新的 MDT 会诊会话。

    Args:
        body: 会诊信息（标题、问题、背景、参与者）。

    Returns:
        创建的会诊会话 ID 及参与者数量。
    """
    uid = int(current_user["sub"])
    n = _now()
    sessions_repo = MdtSessionsRepository(db)
    participants_repo = MdtParticipantsRepository(db)
    roles_repo = AgentRolesRepository(db)
    sid = sessions_repo.create(
        {
            "title": body.title,
            "question": body.question,
            "context": body.context,
            "status": "active",
            "created_by": uid,
            "created_at": n,
            "updated_at": n,
        }
    )
    parts = body.participants
    if not parts:
        roles = roles_repo.list_active(limit=5)
        parts = [
            ParticipantDef(
                agent_role_id=r["id"],
                role_name=r["name"],
                stance="neutral",
                vote_weight=1.0,
            )
            for r in roles
        ]
    for p in parts:
        participants_repo.create_raw(
            {
                "session_id": sid,
                "agent_role_id": p.agent_role_id,
                "role_name": p.role_name,
                "stance": p.stance,
                "vote_weight": p.vote_weight,
                "created_at": n,
            }
        )
    return success({"id": sid, "title": body.title, "participant_count": len(parts)})


@router.get("/sessions")
def list_sessions(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(require_scope("visit")),
    db=Depends(get_db),
):
    """分页查询会诊会话列表。

    Args:
        status_filter: 按状态筛选。
        page/page_size: 分页参数。

    Returns:
        分页的会话列表。
    """
    sessions_repo = MdtSessionsRepository(db)
    conditions, params = [], []
    if status_filter:
        conditions.append("status=?")
        params.append(status_filter)
    total, total_pages, items = sessions_repo.paginate(
        page=page,
        page_size=page_size,
        conditions=conditions or None,
        params=params or None,
        order_by="created_at DESC",
    )
    return success(
        {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    )


@router.get("/sessions/{session_id}")
def get_session(session_id: int, current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    """获取会诊会话详情，含参与者和意见。

    Args:
        session_id: 会话 ID。

    Returns:
        会话详情、参与者列表、意见列表。
    """
    sessions_repo = MdtSessionsRepository(db)
    participants_repo = MdtParticipantsRepository(db)
    opinions_repo = MdtOpinionsRepository(db)
    s = sessions_repo.get_by_id(session_id)
    if not s:
        _n404("MDT Session")
    parts = participants_repo.list_by_session(session_id)
    opinions = opinions_repo.list_by_session(session_id)
    return success({"session": s, "participants": parts, "opinions": opinions})


@router.post("/sessions/{session_id}/debate")
def debate(
    session_id: int,
    body: DebateRequest,
    request: Request,
    current_user=Depends(require_scope("visit")),
    db=Depends(get_db),
):
    """在会话中执行多轮 Multi-Disciplinary 辩论。

    Args:
        session_id: 会话 ID。
        body: 最大辩论轮数。

    Returns:
        当前轮次及各参与者结果。
    """
    sessions_repo = MdtSessionsRepository(db)
    participants_repo = MdtParticipantsRepository(db)
    opinions_repo = MdtOpinionsRepository(db)
    roles_repo = AgentRolesRepository(db)
    s = sessions_repo.get_by_id(session_id)
    if not s:
        _n404("MDT Session")
    if s["status"] == "completed":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Session already completed")
    participants = participants_repo.list_by_session(session_id)
    if not participants:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No participants in session")
    auth = request.headers.get("Authorization", "")
    current_round = s["round_count"] or 0
    results = []
    for _ in range(body.max_rounds):
        current_round += 1
        prev = opinions_repo.build_round_summary(session_id, current_round - 1)
        for p in participants:
            role = roles_repo.get_system_prompt(p["agent_role_id"])
            if not role:
                continue
            json_fmt = (
                "\n\n请以JSON格式输出你的观点："
                '{"opinion":"你的详细观点","summary":"一句话总结",'
                '"sentiment":"positive/negative/neutral/constructive/mixed/analytical",'
                '"confidence":0.0-1.0,"key_points":["要点1","要点2"]}'
            )
            sys_msg = role["system_prompt"] + json_fmt
            user_msg = f"问题：{s['question']}\n背景：{s['context']}"
            if prev:
                user_msg += f"\n\n上一轮各方观点摘要：\n{prev}"
            try:
                ai = _call_ai(
                    [
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": user_msg},
                    ],
                    auth,
                )
                reply = ai.get("reply", "")
                parsed = _parse_json(reply, {})
                if isinstance(parsed, dict):
                    opinion = parsed.get("opinion", reply)
                    summary = parsed.get("summary", "")
                    sentiment = parsed.get("sentiment", "neutral")
                    confidence = float(parsed.get("confidence", 0.5))
                    key_points = json.dumps(parsed.get("key_points", []), ensure_ascii=False)
                else:
                    opinion = reply
                    summary = ""
                    sentiment = "neutral"
                    confidence = 0.5
                    key_points = "[]"
                opinions_repo.create_raw(
                    {
                        "session_id": session_id,
                        "participant_id": p["id"],
                        "round_number": current_round,
                        "opinion": opinion,
                        "summary": summary,
                        "sentiment": sentiment,
                        "confidence": confidence,
                        "key_points": key_points,
                        "ai_response_raw": reply,
                        "tokens_used": ai.get("usage", {}).get("total_tokens", 0),
                        "created_at": _now(),
                    }
                )
                results.append(
                    {
                        "participant_id": p["id"],
                        "round": current_round,
                        "sentiment": sentiment,
                        "confidence": confidence,
                    }
                )
            except Exception:
                results.append(
                    {
                        "participant_id": p["id"],
                        "round": current_round,
                        "error": "AI call failed",
                    }
                )
    sessions_repo.update_fields(session_id, {"round_count": current_round, "updated_at": _now()})
    return success({"round": current_round, "results": results})


@router.post("/sessions/{session_id}/consensus")
def consensus(
    session_id: int,
    request: Request,
    current_user=Depends(require_scope("visit")),
    db=Depends(get_db),
):
    """基于各方辩论意见生成综合共识报告。

    Args:
        session_id: 会话 ID。

    Returns:
        共识结论及结构化 JSON。
    """
    sessions_repo = MdtSessionsRepository(db)
    opinions_repo = MdtOpinionsRepository(db)
    s = sessions_repo.get_by_id(session_id)
    if not s:
        _n404("MDT Session")
    if s["status"] == "completed":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Consensus already generated")
    all_ops = opinions_repo.list_by_session_with_participant(session_id)
    if not all_ops:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No opinions to build consensus from")
    opinions_text = "\n".join(f"[Round {o['round_number']}] {o['role_name']}({o.get('stance', 'neutral')}): {o['opinion']}" for o in all_ops)
    sys_msg = (
        "你是一名MDT辩论主持人，负责总结多方观点形成共识。"
        "请基于以下各方辩论意见，生成综合共识报告。"
        '以JSON格式输出：{"consensus":"综合共识结论","confidence":0.0-1.0,'
        '"agreements":["各方一致认同的点"],"disagreements":["存在分歧的点"],'
        '"action_items":["建议下一步行动"]}'
    )
    user_msg = f"议题：{s['title']}\n问题：{s['question']}\n背景：{s['context']}\n\n各方观点：\n{opinions_text}"
    try:
        ai = _call_ai(
            [
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": user_msg},
            ],
            request.headers.get("Authorization", ""),
        )
        reply = ai.get("reply", "")
        parsed = _parse_json(reply, {})
        if isinstance(parsed, dict):
            consensus_text = parsed.get("consensus", reply)
            consensus_json = json.dumps(parsed, ensure_ascii=False)
        else:
            consensus_text = reply
            consensus_json = json.dumps({"consensus": reply}, ensure_ascii=False)
        sessions_repo.update_fields(
            session_id,
            {
                "consensus": consensus_text,
                "consensus_json": consensus_json,
                "status": "completed",
                "updated_at": _now(),
            },
        )
    except Exception:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail="Failed to generate consensus")
    return success({"consensus": consensus_text, "consensus_json": _parse_json(consensus_json, {})})


@router.get("/sessions/{session_id}/opinions")
def get_opinions(
    session_id: int,
    round_number: Optional[int] = Query(None),
    current_user=Depends(require_scope("visit")),
    db=Depends(get_db),
):
    """获取会诊会话中的意见列表。

    Args:
        session_id: 会话 ID。
        round_number: 可选，按轮次筛选。

    Returns:
        意见列表。
    """
    sessions_repo = MdtSessionsRepository(db)
    opinions_repo = MdtOpinionsRepository(db)
    s = sessions_repo.get_by_id(session_id)
    if not s:
        _n404("MDT Session")
    rows = opinions_repo.list_by_session_with_participant(session_id)
    if round_number is not None:
        rows = [r for r in rows if r.get("round_number") == round_number]
    return success(rows)


@router.get("/sessions/{session_id}/timeline")
def timeline(session_id: int, current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    """获取会诊的时间线视图，按轮次组织。

    Args:
        session_id: 会话 ID。

    Returns:
        会话时间线，含各轮意见及共识（如已完成）。
    """
    sessions_repo = MdtSessionsRepository(db)
    opinions_repo = MdtOpinionsRepository(db)
    s = sessions_repo.get_by_id(session_id)
    if not s:
        _n404("MDT Session")
    opinions = opinions_repo.list_by_session_with_participant(session_id)
    rounds: dict = {}
    for o in opinions:
        rn = str(o["round_number"])
        rounds.setdefault(rn, []).append(o)
    timeline_data = {
        "session": s,
        "rounds": [{"round_number": int(k), "opinions": v} for k, v in sorted(rounds.items(), key=lambda x: int(x[0]))],
    }
    if s["status"] == "completed" and s.get("consensus"):
        timeline_data["consensus"] = {
            "text": s["consensus"],
            "detail": _parse_json(s.get("consensus_json"), {}),
            "updated_at": s["updated_at"],
        }
    return success(timeline_data)


@router.get("/dashboard")
def dashboard(current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    """获取 MDT 会诊仪表盘统计。

    Returns:
        会话总数、完成数、状态分布、平均参与者数等。
    """
    sessions_repo = MdtSessionsRepository(db)
    participants_repo = MdtParticipantsRepository(db)
    opinions_repo = MdtOpinionsRepository(db)
    total = sessions_repo.count()
    completed = sessions_repo.count_completed()
    by_status = sessions_repo.count_by_field("status")
    avg_parts = participants_repo.avg_per_session()
    avg_rounds = sessions_repo.avg_field("round_count")
    avg_confidence = opinions_repo.avg_confidence()
    recent = sessions_repo.list_recent(limit=5)
    return success(
        {
            "total_sessions": total,
            "completed_sessions": completed,
            "by_status": by_status,
            "avg_participants": avg_parts,
            "avg_rounds": avg_rounds,
            "avg_consensus_confidence": avg_confidence,
            "recent_5": recent,
        }
    )
