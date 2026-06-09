"""靶点-管线关联图谱服务。"""

from collections import defaultdict
from typing import Optional

from fastapi import HTTPException
from starlette import status

from pharma_intel.app.schemas.target_pipeline import (
    PipelinePhase,
    PipelineProduct,
    Target,
    TargetPipelineTree,
)

PHASE_COLORS = {
    PipelinePhase.PHASE1: "#94A3B8",
    PipelinePhase.PHASE2: "#60A5FA",
    PipelinePhase.PHASE3: "#F59E0B",
    PipelinePhase.NDA: "#8B5CF6",
    PipelinePhase.APPROVED: "#22C55E",
}

TARGETS = [
    Target(
        id="tgt-pd1",
        name="PD-1",
        gene="PDCD1",
        pathway="Immune checkpoint",
        disease_area="tumor",
        phase="Approved",
        mechanism="解除T细胞免疫抑制，增强抗肿瘤免疫反应",
    ),
    Target(
        id="tgt-egfr",
        name="EGFR",
        gene="EGFR",
        pathway="RTK/RAS/MAPK",
        disease_area="tumor",
        phase="Approved",
        mechanism="抑制EGFR驱动的肿瘤细胞增殖信号",
    ),
    Target(
        id="tgt-btk",
        name="BTK",
        gene="BTK",
        pathway="B-cell receptor signaling",
        disease_area="hematology",
        phase="Approved",
        mechanism="阻断BCR信号传导，抑制恶性B细胞存活",
    ),
    Target(
        id="tgt-cldn18-2",
        name="CLDN18.2",
        gene="CLDN18",
        pathway="Tight junction",
        disease_area="tumor",
        phase="NDA",
        mechanism="靶向胃癌等实体瘤细胞表面紧密连接蛋白亚型",
    ),
]

PIPELINE_PRODUCTS = [
    PipelineProduct(
        id="prod-pembro",
        target_id="tgt-pd1",
        product_name="Pembrolizumab",
        company="Merck",
        phase=PipelinePhase.APPROVED,
        mechanism="Anti-PD-1 antibody",
        moa="阻断PD-1与PD-L1/PD-L2结合，恢复T细胞活性",
        color_code=PHASE_COLORS[PipelinePhase.APPROVED],
        indication="NSCLC",
    ),
    PipelineProduct(
        id="prod-tori",
        target_id="tgt-pd1",
        product_name="Toripalimab",
        company="Junshi Biosciences",
        phase=PipelinePhase.APPROVED,
        mechanism="Anti-PD-1 antibody",
        moa="高亲和力结合PD-1，解除免疫检查点抑制",
        color_code=PHASE_COLORS[PipelinePhase.APPROVED],
        indication="Nasopharyngeal carcinoma",
    ),
    PipelineProduct(
        id="prod-osi",
        target_id="tgt-egfr",
        product_name="Osimertinib",
        company="AstraZeneca",
        phase=PipelinePhase.APPROVED,
        mechanism="EGFR TKI",
        moa="选择性抑制EGFR敏感突变和T790M耐药突变",
        color_code=PHASE_COLORS[PipelinePhase.APPROVED],
        indication="NSCLC",
    ),
    PipelineProduct(
        id="prod-amivantamab",
        target_id="tgt-egfr",
        product_name="Amivantamab",
        company="Johnson & Johnson",
        phase=PipelinePhase.PHASE3,
        mechanism="EGFR/MET bispecific antibody",
        moa="双靶点阻断EGFR和MET通路并诱导免疫介导清除",
        color_code=PHASE_COLORS[PipelinePhase.PHASE3],
        indication="NSCLC",
    ),
    PipelineProduct(
        id="prod-zanu",
        target_id="tgt-btK",
        product_name="Zanubrutinib",
        company="BeiGene",
        phase=PipelinePhase.APPROVED,
        mechanism="BTK inhibitor",
        moa="共价抑制BTK，降低B细胞恶性克隆生存信号",
        color_code=PHASE_COLORS[PipelinePhase.APPROVED],
        indication="Mantle cell lymphoma",
    ),
    PipelineProduct(
        id="prod-ct041",
        target_id="tgt-cldn18-2",
        product_name="CT041",
        company="CARsgen Therapeutics",
        phase=PipelinePhase.PHASE2,
        mechanism="CLDN18.2 CAR-T",
        moa="工程化T细胞识别CLDN18.2阳性实体瘤细胞并杀伤",
        color_code=PHASE_COLORS[PipelinePhase.PHASE2],
        indication="Gastric cancer",
    ),
    PipelineProduct(
        id="prod-zolbeta",
        target_id="tgt-cldn18-2",
        product_name="Zolbetuximab",
        company="Astellas",
        phase=PipelinePhase.NDA,
        mechanism="Anti-CLDN18.2 antibody",
        moa="结合CLDN18.2并通过ADCC/CDC诱导肿瘤细胞死亡",
        color_code=PHASE_COLORS[PipelinePhase.NDA],
        indication="Gastric cancer",
    ),
]


def list_targets(disease_area: Optional[str] = None) -> list[Target]:
    if not disease_area:
        return TARGETS
    needle = disease_area.lower()
    return [target for target in TARGETS if target.disease_area.lower() == needle]


def get_target(target_id: str) -> Target:
    for target in TARGETS:
        if target.id == target_id:
            return target
    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Target not found")


def get_pipeline_products(target_id: str) -> list[PipelineProduct]:
    get_target(target_id)
    return [product for product in PIPELINE_PRODUCTS if product.target_id == target_id]


def get_target_pipeline_tree(
    target_id: Optional[str] = None,
    disease_area: Optional[str] = None,
) -> TargetPipelineTree:
    targets = [get_target(target_id)] if target_id else list_targets(disease_area)
    target_ids = {target.id for target in targets}
    products = [product for product in PIPELINE_PRODUCTS if product.target_id in target_ids]

    products_by_target: dict[str, dict[str, list[PipelineProduct]]] = defaultdict(lambda: defaultdict(list))
    for product in products:
        products_by_target[product.target_id][product.indication].append(product)

    tree_targets = []
    for target in targets:
        indications = []
        for indication, indication_products in sorted(products_by_target[target.id].items()):
            indications.append(
                {
                    "indication": indication,
                    "products": [product.model_dump(mode="json") for product in indication_products],
                }
            )
        tree_targets.append(
            {
                **target.model_dump(),
                "indications": indications,
                "pipeline_count": sum(len(item["products"]) for item in indications),
            }
        )

    return TargetPipelineTree(targets=tree_targets)
