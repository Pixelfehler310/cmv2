from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.identity.dependencies import get_current_active_user
from src.identity.models import User
from src.systems.dnd5e.application.character_sheet_service import CharacterSheetProjectionService
from src.systems.dnd5e.application.character_service import (
    CharacterWriteApplicationService,
    CharacterWriteDenied,
    CharacterWritePayload,
)
from src.systems.dnd5e.content.api.ws_events import ContentStreamWsHandler

router = APIRouter(prefix="/api/characters", tags=["DND5E Characters"])


class CharacterCommandEnvelope(BaseModel):
    request_id: str
    status: str
    reason_code: str | None = None
    catalog_revision: int | None = None
    payload: Any = None


_character_stream_ws_handler = ContentStreamWsHandler()


def get_character_stream_handler() -> ContentStreamWsHandler:
    return _character_stream_ws_handler


def _resolve_request_id(request: Request) -> str:
    return request.headers.get("x-request-id") or uuid4().hex


def _status_code_for_reason(reason_code: str) -> int:
    if reason_code in {
        "CAMPAIGN_OWNERSHIP_VIOLATION",
        "PLAYER_OWNERSHIP_VIOLATION",
        "CAMPAIGN_MEMBERSHIP_REQUIRED",
    }:
        return 403
    if reason_code in {"CHARACTER_NOT_FOUND"}:
        return 404
    return 400


def _status_code_for_sheet_result(status: str, reason_code: str | None) -> int:
    if reason_code == "CHARACTER_NOT_FOUND":
        return 404
    if status == "invalidated":
        return 409
    if status == "denied":
        return 400
    return 200


@router.post("")
async def create_character(
    payload: CharacterWritePayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    request_id = _resolve_request_id(request)
    service = CharacterWriteApplicationService(db)

    try:
        created = await service.create_character(payload, current_user=current_user)
        return CharacterCommandEnvelope(
            request_id=request_id,
            status="resolved",
            payload=created.model_dump(mode="json"),
        )
    except CharacterWriteDenied as exc:
        envelope = CharacterCommandEnvelope(
            request_id=request_id,
            status="denied",
            reason_code=exc.code,
            payload={
                "message": exc.message,
                "unresolved_reference_ids": exc.unresolved_reference_ids,
            },
        )
        return JSONResponse(
            status_code=_status_code_for_reason(exc.code),
            content=envelope.model_dump(mode="json"),
        )


@router.put("/{character_id}")
async def update_character(
    character_id: str,
    payload: CharacterWritePayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    request_id = _resolve_request_id(request)
    service = CharacterWriteApplicationService(db)

    try:
        updated = await service.update_character(
            character_id,
            payload,
            current_user=current_user,
        )
        return CharacterCommandEnvelope(
            request_id=request_id,
            status="resolved",
            payload=updated.model_dump(mode="json"),
        )
    except CharacterWriteDenied as exc:
        envelope = CharacterCommandEnvelope(
            request_id=request_id,
            status="denied",
            reason_code=exc.code,
            payload={
                "message": exc.message,
                "unresolved_reference_ids": exc.unresolved_reference_ids,
            },
        )
        return JSONResponse(
            status_code=_status_code_for_reason(exc.code),
            content=envelope.model_dump(mode="json"),
        )


@router.get("/{character_id}/sheet")
async def get_character_sheet_projection(
    character_id: str,
    request: Request,
    catalog_revision: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    ws_handler: ContentStreamWsHandler = Depends(get_character_stream_handler),
    current_user: User = Depends(get_current_active_user),
):
    del current_user
    request_id = _resolve_request_id(request)
    service = CharacterSheetProjectionService(db)

    try:
        projection = await service.project_character_sheet(
            character_id,
            catalog_revision=catalog_revision,
        )
    except CharacterWriteDenied as exc:
        envelope = CharacterCommandEnvelope(
            request_id=request_id,
            status="denied",
            reason_code=exc.code,
            catalog_revision=catalog_revision,
            payload={
                "message": exc.message,
                "unresolved_reference_ids": exc.unresolved_reference_ids,
            },
        )
        return JSONResponse(
            status_code=_status_code_for_reason(exc.code),
            content=envelope.model_dump(mode="json"),
        )

    if projection.resolution_status == "resolved":
        await ws_handler.emit_character_sheet_projection_updated(
            campaign_id=projection.campaign_id,
            request_id=request_id,
            character_id=projection.character_id,
            sheet_revision=projection.sheet_revision,
            catalog_revision=projection.catalog_revision,
        )
    elif projection.resolution_status == "denied":
        await ws_handler.emit_character_sheet_references_denied(
            campaign_id=projection.campaign_id,
            request_id=request_id,
            character_id=projection.character_id,
            sheet_revision=projection.sheet_revision,
            reason_code=projection.denial_reason_code or "MISSING_REQUIRED_FIELD",
            unresolved_reference_ids=projection.unresolved_reference_ids,
        )
    elif projection.resolution_status == "invalidated":
        await ws_handler.emit_character_sheet_invalidation_required(
            campaign_id=projection.campaign_id,
            request_id=request_id,
            character_id=projection.character_id,
            invalidated_at_revision=projection.sheet_revision,
            reason_code=projection.denial_reason_code or "CATALOG_REVISION_MISMATCH",
        )

    envelope = CharacterCommandEnvelope(
        request_id=request_id,
        status=projection.resolution_status,
        reason_code=projection.denial_reason_code,
        catalog_revision=projection.catalog_revision,
        payload=projection.model_dump(mode="json"),
    )
    return JSONResponse(
        status_code=_status_code_for_sheet_result(
            projection.resolution_status,
            projection.denial_reason_code,
        ),
        content=envelope.model_dump(mode="json"),
    )
