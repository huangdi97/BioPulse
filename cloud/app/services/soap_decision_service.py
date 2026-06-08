"""SOAP决策服务处理结构化评估与决策逻辑。"""

import json
from typing import Optional

from fastapi import HTTPException
from starlette import status as http_status

from cloud.app.repositories import (
    AsyncMdtOpinionsRepository,
    SoapDecisionsRepository,
    SoapTemplatesRepository,
)
from cloud.app.services.base import BaseService
from shared.base import PaginatedResponse, validate_columns
from shared.columns import TABLE_SOAP_DECISIONS_COLS


def _row(row, json_keys=None):
    """将数据库行转为字典并解析指定的 JSON 字段。

    Args:
        row: 数据库行
        json_keys: 需解析为 JSON 的字段名列表

    Returns:
        转换后的字典，None 输入返回 None
    """
    if row is None:
        return None
    d = dict(row)
    for k in json_keys or []:
        if k in d and isinstance(d[k], str):
            d[k] = json.loads(d[k])
    return d


class SoapDecisionService(BaseService):
    """SOAP决策服务，提供模板管理、决策 CRUD、意见征询与最终裁定功能。"""

    def create_template(self, name: str, category: str, description: str, structure: dict, created_by) -> dict:
        """创建 SOAP 决策模板。

        Args:
            name: 模板名称
            category: 分类
            description: 描述
            structure: 结构化模板定义
            created_by: 创建者 ID

        Returns:
            创建的模板记录
        """
        templates_repo = SoapTemplatesRepository(self.db)
        tmpl_id = templates_repo.create(
            {
                "name": name,
                "category": category,
                "description": description,
                "structure": json.dumps(structure, ensure_ascii=False),
                "created_by": created_by,
                "updated_at": "NOW()",
            }
        )
        templates_repo.execute("UPDATE soap_templates SET updated_at=NOW() WHERE id=?", (tmpl_id,))
        self.db.commit()
        row = templates_repo.get_by_id(tmpl_id)
        return _row(row, ["structure"])

    def list_templates(self, category: Optional[str] = None) -> list:
        """列出有效模板。

        Args:
            category: 按分类筛选

        Returns:
            模板列表
        """
        templates_repo = SoapTemplatesRepository(self.db)
        rows = templates_repo.list_active(category=category)
        return [_row(r, ["structure"]) for r in rows]

    def create_decision(
        self,
        title: str,
        template_id: Optional[int],
        subjective: str,
        objective: str,
        assessment: str,
        plan: str,
        priority: str,
        tags: list,
        created_by,
    ) -> dict:
        """创建 SOAP 决策记录（S-O-A-P 四要素）。

        Args:
            title: 决策标题
            template_id: 关联模板 ID
            subjective: 主观信息（S）
            objective: 客观信息（O）
            assessment: 评估（A）
            plan: 计划（P）
            priority: 优先级
            tags: 标签列表
            created_by: 创建者 ID

        Returns:
            创建的决策记录
        """
        templates_repo = SoapTemplatesRepository(self.db)
        decisions_repo = SoapDecisionsRepository(self.db)
        if template_id:
            tmpl = templates_repo.get_by_id(template_id)
            if not tmpl or not tmpl.get("is_active"):
                raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Template not found")
        dec_id = decisions_repo.create(
            {
                "title": title,
                "template_id": template_id,
                "subjective": subjective,
                "objective": objective,
                "assessment": assessment,
                "plan": plan,
                "priority": priority,
                "tags": json.dumps(tags, ensure_ascii=False),
                "created_by": created_by,
                "updated_at": "NOW()",
            }
        )
        decisions_repo.execute("UPDATE soap_decisions SET updated_at=NOW() WHERE id=?", (dec_id,))
        self.db.commit()
        row = decisions_repo.get_by_id(dec_id)
        return _row(row, ["tags"])

    def list_decisions(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        tag: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """分页查询决策列表。

        Args:
            status: 按状态筛选
            priority: 按优先级筛选
            tag: 按标签筛选
            page: 页码
            page_size: 每页条数

        Returns:
            分页决策列表
        """
        decisions_repo = SoapDecisionsRepository(self.db)
        total, tp, items = decisions_repo.list_active_filtered(status=status, priority=priority, tag=tag, page=page, page_size=page_size)
        return PaginatedResponse(
            items=[_row(r, ["tags"]) for r in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=tp,
        )

    def get_decision(self, decision_id: int) -> dict:
        """获取决策详情。

        Args:
            decision_id: 决策 ID

        Returns:
            决策记录
        """
        decisions_repo = SoapDecisionsRepository(self.db)
        row = decisions_repo.get_by_id(decision_id)
        if not row or not row.get("is_active"):
            raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Decision not found")
        return _row(row, ["tags"])

    def update_decision(
        self,
        decision_id: int,
        subjective: Optional[str] = None,
        objective: Optional[str] = None,
        assessment: Optional[str] = None,
        plan: Optional[str] = None,
        priority: Optional[str] = None,
        tags: Optional[list] = None,
    ) -> dict:
        """更新决策字段。

        Args:
            decision_id: 决策 ID
            subjective: 新主观信息
            objective: 新客观信息
            assessment: 新评估
            plan: 新计划
            priority: 新优先级
            tags: 新标签

        Returns:
            更新后的决策记录
        """
        decisions_repo = SoapDecisionsRepository(self.db)
        row = decisions_repo.get_by_id(decision_id)
        if not row or not row.get("is_active"):
            raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Decision not found")
        updates = {}
        for f in ("subjective", "objective", "assessment", "plan", "priority"):
            v = locals().get(f)
            if v is not None:
                updates[f] = v
        if tags is not None:
            updates["tags"] = json.dumps(tags, ensure_ascii=False)
        if updates:
            updates["updated_at"] = "NOW()"
            validate_columns(updates, "soap_decisions", TABLE_SOAP_DECISIONS_COLS)
            updates_to_save = {k: v for k, v in updates.items() if v != "NOW()"}
            decisions_repo.update(decision_id, updates_to_save)
            decisions_repo.execute("UPDATE soap_decisions SET updated_at=NOW() WHERE id=?", (decision_id,))
            self.db.commit()
        row = decisions_repo.get_by_id(decision_id)
        return _row(row, ["tags"])

    def submit_decision(self, decision_id: int) -> dict:
        """提交决策进入意见收集状态。

        Args:
            decision_id: 决策 ID

        Returns:
            更新后的决策记录
        """
        decisions_repo = SoapDecisionsRepository(self.db)
        row = decisions_repo.get_by_id(decision_id)
        if not row or not row.get("is_active"):
            raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Decision not found")
        if row["status"] != "draft":
            raise HTTPException(
                http_status.HTTP_400_BAD_REQUEST,
                detail="Only draft decisions can be submitted",
            )
        decisions_repo.update(decision_id, {"status": "collecting"})
        decisions_repo.execute("UPDATE soap_decisions SET updated_at=NOW() WHERE id=?", (decision_id,))
        self.db.commit()
        row = decisions_repo.get_by_id(decision_id)
        return _row(row, ["tags"])

    def add_opinion(
        self,
        decision_id: int,
        opinion: str,
        stance: str,
        supporting_data: str,
        confidence: float,
        attachments: list,
        user_id,
        role: str,
    ) -> dict:
        """为决策添加异步 MDT 意见。

        Args:
            decision_id: 决策 ID
            opinion: 意见内容
            stance: 立场（support/oppose/neutral）
            supporting_data: 支撑数据
            confidence: 置信度
            attachments: 附件列表
            user_id: 提交者 ID
            role: 提交者角色

        Returns:
            创建的意见记录
        """
        decisions_repo = SoapDecisionsRepository(self.db)
        opinions_repo = AsyncMdtOpinionsRepository(self.db)
        dec = decisions_repo.get_by_id(decision_id)
        if not dec or not dec.get("is_active"):
            raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Decision not found")
        opinion_id = opinions_repo.create(
            {
                "decision_id": decision_id,
                "contributor_id": user_id,
                "contributor_role": role,
                "opinion": opinion,
                "supporting_data": supporting_data,
                "stance": stance,
                "confidence": confidence,
                "attachments": json.dumps(attachments, ensure_ascii=False),
                "updated_at": "NOW()",
            }
        )
        opinions_repo.execute("UPDATE async_mdt_opinions SET updated_at=NOW() WHERE id=?", (opinion_id,))
        self.db.commit()
        row = opinions_repo.get_by_id(opinion_id)
        return _row(row, ["attachments"])

    def list_opinions(self, decision_id: int) -> list:
        """列出决策的所有异步意见。

        Args:
            decision_id: 决策 ID

        Returns:
            意见列表
        """
        decisions_repo = SoapDecisionsRepository(self.db)
        opinions_repo = AsyncMdtOpinionsRepository(self.db)
        dec = decisions_repo.get_by_id(decision_id)
        if not dec or not dec.get("is_active"):
            raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Decision not found")
        rows = opinions_repo.list_by_decision(decision_id)
        return [_row(r, ["attachments"]) for r in rows]

    def finalize_decision(self, decision_id: int, decision_summary: str, user_id) -> dict:
        """最终裁定决策，写入摘要和裁定者。

        Args:
            decision_id: 决策 ID
            decision_summary: 裁定摘要
            user_id: 裁定者 ID

        Returns:
            已裁定的决策记录
        """
        decisions_repo = SoapDecisionsRepository(self.db)
        row = decisions_repo.get_by_id(decision_id)
        if not row or not row.get("is_active"):
            raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Decision not found")
        if row["status"] != "collecting":
            raise HTTPException(
                http_status.HTTP_400_BAD_REQUEST,
                detail="Only decisions in 'collecting' status can be finalized",
            )
        decisions_repo.update(
            decision_id,
            {
                "decision_summary": decision_summary,
                "status": "decided",
                "decided_by": user_id,
            },
        )
        decisions_repo.execute(
            "UPDATE soap_decisions SET decided_at=NOW(), updated_at=NOW() WHERE id=?",
            (decision_id,),
        )
        self.db.commit()
        row = decisions_repo.get_by_id(decision_id)
        return _row(row, ["tags"])

    def dashboard(self) -> dict:
        """SOAP 决策仪表盘，汇总决策与意见统计。

        Returns:
            含总数、状态分布、优先级分布和最近决策的字典
        """
        decisions_repo = SoapDecisionsRepository(self.db)
        opinions_repo = AsyncMdtOpinionsRepository(self.db)
        total = decisions_repo.count_active()
        by_status = decisions_repo.count_by_status()
        by_priority = decisions_repo.count_by_priority()
        total_opinions = opinions_repo.count_all()
        recent = decisions_repo.list_active_recent(5)
        return {
            "total_decisions": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "total_opinions": total_opinions,
            "recent_decisions": [_row(r, ["tags"]) for r in recent],
        }
