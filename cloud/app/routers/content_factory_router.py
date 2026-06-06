"""内容工厂路由：模板创建、渲染、合规检查与模板列表。"""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from cloud.app.services.content_factory_service import ContentFactoryService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/content-factory", tags=["内容工厂"])


class CreateTemplateRequest(BaseModel):
    """CreateTemplateRequest 服务类。"""

    template_key: str
    name: str = ""
    content_type: str = "text"
    template_body: str = ""
    compliance_rules: str = "[]"
    variables: str = "{}"


class RenderRequest(BaseModel):
    """RenderRequest 服务类。"""

    template_key: str
    variables: dict = {}


@router.post("", summary="Create Template")
def create_template(
    body: CreateTemplateRequest,
    current_user: dict = Depends(require_scope("visit")),
    service: ContentFactoryService = Depends(),
) -> Any:
    """创建内容模板"""
    result = service.create_template(
        template_key=body.template_key,
        name=body.name,
        content_type=body.content_type,
        template_body=body.template_body,
        compliance_rules=body.compliance_rules,
        variables=body.variables,
    )
    return success(data=result)


@router.post("/render", summary="Render Template")
def render_template(
    body: RenderRequest,
    current_user: dict = Depends(require_scope("visit")),
    service: ContentFactoryService = Depends(),
) -> Any:
    """渲染模板并执行合规检查"""
    result = service.render(
        template_key=body.template_key,
        variables=body.variables,
    )
    return success(data=result)


@router.get("", summary="List all Templates")
def list_templates(
    current_user: dict = Depends(require_scope("visit")),
    service: ContentFactoryService = Depends(),
) -> Any:
    """列出所有内容模板"""
    return success(data=service.list_templates())
