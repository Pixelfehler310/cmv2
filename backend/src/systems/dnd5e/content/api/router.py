from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.systems.dnd5e.content.application.services import CompendiumApplicationService
from src.systems.dnd5e.content.domain.definition_models import (
    AbilityDefinition,
    BackgroundDefinition,
    ClassDefinition,
    ConditionDefinition,
    ItemDefinition,
    LoreDefinition,
    MonsterDefinition,
    SpeciesDefinition,
    SpellDefinition,
)
from src.systems.dnd5e.content.domain.errors import (
    CompendiumDomainError,
    ContentPackNotFoundError,
)
from src.systems.dnd5e.content.domain.invariants import CompendiumErrorCode
from src.systems.dnd5e.content.domain.pack_models import ContentPackRecord
from src.systems.dnd5e.content.domain.primitives import DefinitionFamily, LifecycleState
from src.systems.dnd5e.content.infrastructure.unit_of_work import CompendiumUnitOfWork
from src.systems.dnd5e.content.policies.lifecycle_transition_policy import ContentLifecycleError

from .ws_events import ContentStreamWsHandler

router = APIRouter(prefix="/api/compendium", tags=["Compendium"])


DefinitionPayload = Annotated[
    (
        LoreDefinition
        | SpeciesDefinition
        | BackgroundDefinition
        | ClassDefinition
        | ConditionDefinition
        | AbilityDefinition
        | SpellDefinition
        | ItemDefinition
        | MonsterDefinition
    ),
    Field(discriminator="family"),
]


class ErrorResponse(BaseModel):
    error: str
    message: str


class CreatePackRequest(BaseModel):
    id: str
    title: str
    author_user_id: str | None = None
    is_homebrew: bool = True
    pack_key: str | None = None
    compatibility_target: str | None = None


class UpdateDefinitionRequest(BaseModel):
    expected_content_version: int = Field(ge=1)
    updates: dict[str, Any]
    campaign_id: str | None = None


class PublishDefinitionRequest(BaseModel):
    campaign_id: str | None = None


class SupersedeDefinitionRequest(BaseModel):
    new_definition_id: str
    campaign_id: str | None = None


_content_stream_ws_handler = ContentStreamWsHandler()


def get_content_stream_handler() -> ContentStreamWsHandler:
    return _content_stream_ws_handler


def get_compendium_service(
    db: AsyncSession = Depends(get_db),
    ws_handler: ContentStreamWsHandler = Depends(get_content_stream_handler),
) -> CompendiumApplicationService:
    return CompendiumApplicationService(
        uow_factory=lambda: CompendiumUnitOfWork(db),
        event_publisher=ws_handler.publish_mutation_event,
    )


def _strip_code_prefix(raw_message: str, *, code: str) -> str:
    prefix = f"{code}: "
    if raw_message.startswith(prefix):
        return raw_message[len(prefix):]
    return raw_message


def _map_domain_exception(exc: Exception) -> HTTPException:
    if isinstance(exc, ValidationError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error=CompendiumErrorCode.VALIDATION_FAILED.value,
                message=str(exc),
            ).model_dump(),
        )

    if isinstance(exc, ContentLifecycleError):
        code = CompendiumErrorCode.INVALID_LIFECYCLE_TRANSITION.value
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                error=code,
                message=_strip_code_prefix(str(exc), code=code),
            ).model_dump(),
        )

    if isinstance(exc, CompendiumDomainError):
        code = exc.code.value
        conflict_codes = {
            CompendiumErrorCode.INVALID_LIFECYCLE_TRANSITION.value,
            CompendiumErrorCode.DEFINITION_ID_CONFLICT.value,
            CompendiumErrorCode.PACK_ID_CONFLICT.value,
            CompendiumErrorCode.DUPLICATE_SLUG.value,
            CompendiumErrorCode.VERSION_MISMATCH.value,
            CompendiumErrorCode.INVALID_REPLACEMENT_TARGET.value,
            CompendiumErrorCode.CYCLE_DETECTED.value,
            CompendiumErrorCode.LINKED_TARGET_IN_USE.value,
            CompendiumErrorCode.ILLEGAL_STATE_DEPENDENCY.value,
        }
        not_found_codes = {
            CompendiumErrorCode.PACK_NOT_FOUND.value,
            CompendiumErrorCode.DEFINITION_NOT_FOUND.value,
            CompendiumErrorCode.LINKED_TARGET_NOT_FOUND.value,
        }

        if code in conflict_codes:
            status_code = status.HTTP_409_CONFLICT
        elif code in not_found_codes:
            status_code = status.HTTP_404_NOT_FOUND
        else:
            status_code = status.HTTP_400_BAD_REQUEST

        return HTTPException(
            status_code=status_code,
            detail=ErrorResponse(
                error=code,
                message=_strip_code_prefix(str(exc), code=code),
            ).model_dump(),
        )

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=ErrorResponse(
            error="INTERNAL_ERROR",
            message="Unhandled compendium error.",
        ).model_dump(),
    )


@router.post("/packs", response_model=ContentPackRecord)
async def create_pack(
    payload: CreatePackRequest,
    service: CompendiumApplicationService = Depends(get_compendium_service),
):
    now = datetime.now(timezone.utc)
    pack = ContentPackRecord(
        id=payload.id,
        author_user_id=payload.author_user_id,
        title=payload.title,
        lifecycle_state=LifecycleState.DRAFT,
        is_homebrew=payload.is_homebrew,
        pack_key=payload.pack_key,
        compatibility_target=payload.compatibility_target,
        created_at=now,
        updated_at=now,
    )

    try:
        return await service.create_pack(pack)
    except Exception as exc:
        raise _map_domain_exception(exc) from exc


@router.get("/packs", response_model=list[ContentPackRecord])
async def list_packs(
    lifecycle_state: LifecycleState | None = Query(default=None),
    service: CompendiumApplicationService = Depends(get_compendium_service),
):
    try:
        return await service.list_packs(lifecycle_state=lifecycle_state)
    except Exception as exc:
        raise _map_domain_exception(exc) from exc


@router.get("/packs/{pack_id}", response_model=ContentPackRecord)
async def get_pack(
    pack_id: str,
    service: CompendiumApplicationService = Depends(get_compendium_service),
):
    try:
        pack = await service.get_pack(pack_id)
        if pack is None:
            raise ContentPackNotFoundError(pack_id)
        return pack
    except Exception as exc:
        raise _map_domain_exception(exc) from exc


@router.post("/definitions", response_model=DefinitionPayload)
async def create_definition(
    payload: DefinitionPayload,
    request: Request,
    campaign_id: str | None = Query(default=None),
    service: CompendiumApplicationService = Depends(get_compendium_service),
):
    try:
        return await service.create_definition(
            payload,
            request_id=request.headers.get("x-request-id"),
            campaign_id=campaign_id,
        )
    except Exception as exc:
        raise _map_domain_exception(exc) from exc


@router.get("/definitions", response_model=list[DefinitionPayload])
async def list_definitions(
    pack_id: str,
    family: DefinitionFamily | None = Query(default=None),
    service: CompendiumApplicationService = Depends(get_compendium_service),
):
    try:
        return await service.list_definitions(pack_id=pack_id, family=family)
    except Exception as exc:
        raise _map_domain_exception(exc) from exc


@router.get("/definitions/{definition_id}", response_model=DefinitionPayload)
async def get_definition(
    definition_id: str,
    service: CompendiumApplicationService = Depends(get_compendium_service),
):
    try:
        return await service.get_definition(definition_id)
    except Exception as exc:
        raise _map_domain_exception(exc) from exc


@router.put("/definitions/{definition_id}", response_model=DefinitionPayload)
async def update_definition(
    definition_id: str,
    payload: UpdateDefinitionRequest,
    request: Request,
    service: CompendiumApplicationService = Depends(get_compendium_service),
):
    try:
        return await service.update_definition(
            definition_id=definition_id,
            updates=payload.updates,
            expected_content_version=payload.expected_content_version,
            request_id=request.headers.get("x-request-id"),
            campaign_id=payload.campaign_id,
        )
    except Exception as exc:
        raise _map_domain_exception(exc) from exc


@router.delete("/definitions/{definition_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_definition(
    definition_id: str,
    request: Request,
    expected_content_version: int = Query(..., ge=1),
    campaign_id: str | None = Query(default=None),
    service: CompendiumApplicationService = Depends(get_compendium_service),
):
    try:
        await service.delete_definition(
            definition_id=definition_id,
            expected_content_version=expected_content_version,
            request_id=request.headers.get("x-request-id"),
            campaign_id=campaign_id,
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as exc:
        raise _map_domain_exception(exc) from exc


@router.post("/definitions/{definition_id}/publish", response_model=DefinitionPayload)
async def publish_definition(
    definition_id: str,
    payload: PublishDefinitionRequest,
    request: Request,
    service: CompendiumApplicationService = Depends(get_compendium_service),
):
    try:
        return await service.publish_definition(
            definition_id=definition_id,
            request_id=request.headers.get("x-request-id"),
            campaign_id=payload.campaign_id,
        )
    except Exception as exc:
        raise _map_domain_exception(exc) from exc


@router.post("/definitions/{definition_id}/supersede", response_model=DefinitionPayload)
async def supersede_definition(
    definition_id: str,
    payload: SupersedeDefinitionRequest,
    request: Request,
    service: CompendiumApplicationService = Depends(get_compendium_service),
):
    try:
        return await service.supersede_definition(
            old_definition_id=definition_id,
            new_definition_id=payload.new_definition_id,
            request_id=request.headers.get("x-request-id"),
            campaign_id=payload.campaign_id,
        )
    except Exception as exc:
        raise _map_domain_exception(exc) from exc
