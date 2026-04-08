from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


ResolutionStatus = Literal["resolved", "denied", "invalidated"]


class SheetProjectionRequest(BaseModel):
    character_id: str
    campaign_id: str
    catalog_revision: int = Field(ge=0)
    correlation_id: str | None = None


class CharacterSheetProjection(BaseModel):
    character_id: str
    campaign_id: str
    catalog_revision: int = Field(ge=0)
    sheet_revision: int = Field(ge=0)
    resolution_status: ResolutionStatus
    computed_fields: dict[str, Any] = Field(default_factory=dict)
    last_resolved_at: datetime
    denial_reason_code: str | None = None
    unresolved_reference_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_resolution_payload(self) -> "CharacterSheetProjection":
        if self.resolution_status == "denied":
            if not self.denial_reason_code:
                raise ValueError("denial_reason_code is required when resolution_status is denied")
            if not self.unresolved_reference_ids:
                raise ValueError(
                    "unresolved_reference_ids is required when resolution_status is denied"
                )
            return self

        if self.resolution_status == "invalidated" and not self.denial_reason_code:
            raise ValueError("denial_reason_code is required when resolution_status is invalidated")

        if self.resolution_status == "resolved":
            if self.denial_reason_code is not None:
                raise ValueError("resolved projection cannot include denial_reason_code")
            if self.unresolved_reference_ids:
                raise ValueError("resolved projection cannot include unresolved_reference_ids")

        return self
