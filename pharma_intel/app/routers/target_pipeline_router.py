"""靶点-管线关联图谱 API。"""

from typing import Optional

from fastapi import APIRouter, Query

from pharma_intel.app.services.target_pipeline_service import (
    get_pipeline_products,
    get_target,
    get_target_pipeline_tree,
    list_targets,
)

router = APIRouter(prefix="/api/targets", tags=["靶点-管线图谱"])


@router.get("", tags=["靶点-管线图谱"])
def targets(disease_area: Optional[str] = Query(None, description="治疗领域筛选")):
    return list_targets(disease_area=disease_area)


@router.get("/{id}", tags=["靶点-管线图谱"])
def target_detail(id: str):
    target = get_target(id)
    pipeline_tree = get_target_pipeline_tree(target_id=id)
    return {
        **target.model_dump(),
        "pipeline": pipeline_tree.targets[0]["indications"],
        "pipeline_count": pipeline_tree.targets[0]["pipeline_count"],
    }


@router.get("/{id}/pipeline", tags=["靶点-管线图谱"])
def target_pipeline(id: str):
    return get_pipeline_products(id)
