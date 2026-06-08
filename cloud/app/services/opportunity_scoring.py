"""Stage probability scoring and transition validation for sales opportunities."""

from cloud.app.repositories import CustomersRepository, OpportunitiesRepository

VALID_STAGES = ["lead", "qualify", "proposal", "negotiation", "won", "lost"]
TERMINAL_STAGES = {"won", "lost"}
STAGE_ORDER = ["lead", "qualify", "proposal", "negotiation", "won", "lost"]


def calc_stage_probability(stage: str) -> int:
    mapping = {
        "lead": 10,
        "qualify": 30,
        "proposal": 50,
        "negotiation": 75,
        "won": 100,
        "lost": 0,
    }
    return mapping.get(stage, 0)


def validate_stage_transition(current: str, target: str) -> None:
    from fastapi import HTTPException
    from starlette import status

    if current in TERMINAL_STAGES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Cannot transition from a terminal stage",
        )


def get_opp_or_404(db, opp_id: int) -> dict:
    from fastapi import HTTPException
    from starlette import status

    opp_repo = OpportunitiesRepository(db)
    rows = opp_repo.list_all(
        conditions=["id=?", "is_active=1"],
        params=[opp_id],
    )
    if not rows:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    return rows[0]


def row_to_dict(db, row) -> dict:
    cust_repo = CustomersRepository(db)
    customer = cust_repo.get_by_id(row["customer_id"])
    return {
        "id": row["id"],
        "customer_id": row["customer_id"],
        "customer_name": customer["name"] if customer else "",
        "name": row["name"],
        "description": row["description"],
        "stage": row["stage"],
        "probability": row["probability"],
        "estimated_value": row["estimated_value"],
        "actual_value": row["actual_value"],
        "assigned_to": row["assigned_to"],
        "close_date": row["close_date"],
        "notes": row["notes"],
        "is_active": row["is_active"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
