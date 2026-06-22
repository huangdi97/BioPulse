"""ExtractionSchema — defines target fields for LLM-based structured extraction."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator


class ExtractionSchema(BaseModel):
    field_name: str
    description: str
    type: str
    enum_options: list[str] | None = None

    @field_validator("type")
    @classmethod
    def _validate_type(cls, v: str) -> str:
        allowed = {"string", "number", "boolean", "enum"}
        if v not in allowed:
            msg = f"Invalid type '{v}': must be one of {allowed}"
            raise ValueError(msg)
        return v

    @field_validator("enum_options")
    @classmethod
    def _validate_enum_options(cls, v: list[str] | None, info: Any) -> list[str] | None:
        if v is not None and info.data.get("type") != "enum":
            raise ValueError("enum_options only allowed when type='enum'")
        return v
