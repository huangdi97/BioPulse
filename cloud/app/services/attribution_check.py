import json

from fastapi import HTTPException
from starlette import status

from cloud.app.services.attribution_calc import _FACTOR_META


class AttributionCheckMixin:
    def get_attribution(self, opp_id: int) -> dict:
        row = self.db.execute(
            "SELECT * FROM opportunity_attributions WHERE opportunity_id=?",
            (opp_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Attribution not found")
        return self._row_to_dict(row)

    def list_factors(self) -> list[dict]:
        return list(_FACTOR_META)

    @staticmethod
    def _row_to_dict(row) -> dict:
        factors_raw = row["factors"]
        if isinstance(factors_raw, str):
            factors = json.loads(factors_raw)
        else:
            factors = factors_raw or []
        return {
            "opportunity_id": row["opportunity_id"],
            "total_score": row["total_score"],
            "confidence": row["confidence"],
            "factors": factors,
            "factor_count": row["factor_count"],
            "top_factor_name": row["top_factor_name"],
            "recommendation": row["recommendation"],
            "model_version": row["model_version"],
            "created_at": row["created_at"],
            "updated_at": row.get("updated_at", ""),
        }
