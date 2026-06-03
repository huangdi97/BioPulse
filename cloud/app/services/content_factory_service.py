import json
import re
from datetime import datetime, timezone

from fastapi import HTTPException
from starlette import status

from cloud.app.services.base import BaseService


def _check_image_compliance(body: str) -> list:
    findings = []
    if "医疗" in body or "治疗" in body:
        findings.append({"rule": "image_claim_check", "passed": False, "message": "图片中不可包含疗效声明"})
    return findings


def _check_text_compliance(body: str, rules: list) -> list:
    findings = []
    for rule in rules:
        rule_key = rule if isinstance(rule, str) else rule.get("key", "unknown")
        keywords = rule if isinstance(rule, str) else rule.get("keywords", [])
        if isinstance(keywords, str):
            keywords = [keywords]
        for kw in keywords:
            if kw in body:
                findings.append(
                    {
                        "rule": rule_key,
                        "passed": False,
                        "message": f"内容包含合规关键词 '{kw}'",
                    }
                )
    return findings


def _render_template(template_body: str, variables: dict) -> str:
    def replace_var(match):
        key = match.group(1)
        return str(variables.get(key, match.group(0)))

    return re.sub(r"\{\{(\w+)\}\}", replace_var, template_body)


class ContentFactoryService(BaseService):
    """ContentFactory 服务类。"""

    def create_template(
        self,
        template_key: str,
        name: str,
        content_type: str,
        template_body: str,
        compliance_rules: str = "[]",
        variables: str = "{}",
    ) -> dict:
        """create_template 操作。

        Args:
            template_key: 描述
            name: 描述
            content_type: 描述
            template_body: 描述
            compliance_rules: 描述
            variables: 描述

        Returns:
            描述
        """
        now = datetime.now(timezone.utc).isoformat()
        try:
            cur = self.db.execute(
                "INSERT INTO content_factory_templates "
                "(template_key, name, content_type, template_body, compliance_rules, variables, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (template_key, name, content_type, template_body, compliance_rules, variables, now),
            )
            self.db.commit()
        except Exception as e:
            if "UNIQUE" in str(e):
                raise HTTPException(status.HTTP_409_CONFLICT, detail=f"模板键 '{template_key}' 已存在")
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        return {
            "id": cur.lastrowid,
            "template_key": template_key,
            "name": name,
            "content_type": content_type,
        }

    def list_templates(self) -> list:
        """list_templates 操作。

        Returns:
            描述
        """
        rows = self.db.execute(
            "SELECT id, template_key, name, content_type, is_active, created_at "
            "FROM content_factory_templates ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def render(self, template_key: str, variables: dict) -> dict:
        """render 操作。

        Args:
            template_key: 描述
            variables: 描述

        Returns:
            描述
        """
        row = self.db.execute(
            "SELECT * FROM content_factory_templates WHERE template_key = ?",
            (template_key,),
        ).fetchone()
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"模板 '{template_key}' 未找到")
        if not row["is_active"]:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="模板已停用")

        body_rendered = _render_template(row["template_body"], variables)
        compliance_rules = json.loads(row["compliance_rules"] or "[]")
        findings = _check_text_compliance(body_rendered, compliance_rules)

        if row["content_type"] == "image":
            image_findings = _check_image_compliance(body_rendered)
            findings.extend(image_findings)

        return {
            "template_key": template_key,
            "content_type": row["content_type"],
            "rendered_body": body_rendered,
            "compliance_findings": findings,
            "compliant": all(f.get("passed", True) for f in findings),
        }
