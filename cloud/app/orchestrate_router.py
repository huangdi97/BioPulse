from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from starlette import status

from cloud.app.services.orchestrate_service import OrchestrateService
from shared.auth import get_current_user
from shared.base import success

router = APIRouter(prefix="/orchestrate", tags=["Orchestration"])


class TemplateCreate(BaseModel):
    template_name: str
    description: str = ""
    steps: list[dict] = []


class OrchestrateRun(BaseModel):
    template_name: str
    context: dict = {}


@router.post("/templates/create", status_code=status.HTTP_201_CREATED)
def create_template(body: TemplateCreate,
                    current_user=Depends(get_current_user),
                    service: OrchestrateService = Depends()):
    uid = int(current_user["sub"])
    row = service.create_template(
        template_name=body.template_name,
        description=body.description,
        steps=body.steps,
        user_id=uid,
    )
    return success(data=row)


@router.get("/templates/list")
def list_templates(
    enabled: Optional[int] = Query(None),
    current_user=Depends(get_current_user),
    service: OrchestrateService = Depends(),
):
    rows = service.list_templates(enabled=enabled)
    return success(data=rows)


@router.post("/run", status_code=status.HTTP_201_CREATED)
def run_orchestration(body: OrchestrateRun,
                      current_user=Depends(get_current_user),
                      service: OrchestrateService = Depends()):
    result = service.run_orchestration(
        template_name=body.template_name,
        context=body.context,
    )
    return success(data=result)
