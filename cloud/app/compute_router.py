# FROZEN — 代码保留不迭代。参见一云四端-整体战略规划-v2.3-final.md 第2章
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from starlette import status

from cloud.app.services.compute_service import ComputeService
from shared.auth import get_current_user
from shared.base import success

router = APIRouter(prefix="/compute", tags=["Privacy Computing"])


class ComputeJobCreate(BaseModel):
    compute_type: str
    sensitivity_level: str = "medium"
    data_summary: str = ""


class FederatedInit(BaseModel):
    model_name: str
    num_rounds: int = 5
    aggregation_method: str = "fed_avg"


class FederatedSubmit(BaseModel):
    round_id: str
    participant_id: str
    metrics: dict = {}
    update_summary: str = ""


class TrustFedProve(BaseModel):
    contribution_id: int


@router.post("/job/create")
def job_create(
    body: ComputeJobCreate,
    current_user: dict = Depends(get_current_user),
    service: ComputeService = Depends(),
):
    user_id = int(current_user["sub"])
    row = service.create_job(
        compute_type=body.compute_type,
        sensitivity_level=body.sensitivity_level,
        data_summary=body.data_summary,
        user_id=user_id,
    )
    return success(data=row)


@router.get("/job/list")
def job_list(
    status: Optional[str] = Query(None),
    compute_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    service: ComputeService = Depends(),
):
    rows = service.list_jobs(status_filter=status, compute_type=compute_type)
    return success(data=rows)


@router.get("/job/{job_id}")
def job_detail(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    service: ComputeService = Depends(),
):
    row = service.get_job(job_id)
    return success(data=row)


@router.post("/federated/init")
def federated_init(
    body: FederatedInit,
    current_user: dict = Depends(get_current_user),
    service: ComputeService = Depends(),
):
    rows = service.init_federated(
        model_name=body.model_name,
        num_rounds=body.num_rounds,
        aggregation_method=body.aggregation_method,
    )
    return success(data=rows)


@router.post("/federated/submit")
def federated_submit(
    body: FederatedSubmit,
    current_user: dict = Depends(get_current_user),
    service: ComputeService = Depends(),
):
    row = service.submit_federated(
        round_id=body.round_id,
        participant_id=body.participant_id,
        metrics=body.metrics,
        update_summary=body.update_summary,
    )
    return success(data=row)


@router.get("/federated/rounds/list")
def rounds_list(
    model_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    service: ComputeService = Depends(),
):
    rows = service.list_federated_rounds(model_name=model_name, status_filter=status)
    return success(data=rows)


@router.post("/trustfed/prove")
def trustfed_prove(
    body: TrustFedProve,
    current_user: dict = Depends(get_current_user),
    service: ComputeService = Depends(),
):
    proof = service.prove_contribution(
        contribution_id=body.contribution_id,
        prover_sub=current_user.get("sub", "unknown"),
    )
    return success(data=proof)


@router.get("/trustfed/verify/{contribution_id}")
def trustfed_verify(
    contribution_id: int,
    current_user: dict = Depends(get_current_user),
    service: ComputeService = Depends(),
):
    result = service.verify_contribution(contribution_id)
    return success(data=result)
