from __future__ import annotations
__production_status__ = "gold"

from datetime import datetime, timezone
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.systems.dnd5e.content.application.resolution import (
    LinkedEntryResolutionService,
    ResolvedLink,
    ResolvedLinkTree,
)
from src.systems.dnd5e.content.application.services import CompendiumApplicationService
from src.systems.dnd5e.content.domain.definition_models import (
    ActionDefinition,
    AbilityDefinition,
    BackgroundDefinition,
    ClassDefinition,
    ConditionDefinition,
    FactionDefinition,
    ItemDefinition,
    LoreDefinition,
    MonsterDefinition,
    PlaceDefinition,
    RegionDefinition,
    SpeciesDefinition,
    SpellDefinition,
)
from src.systems.dnd5e.content.domain.errors import (
    CompendiumDomainError,
    ContentPackNotFoundError,
    GraphCycleError,
)
from src.systems.dnd5e.content.domain.index_models import (
    FAMILY_PAYLOAD_FILTER_KEYS,
    IndexDocument,
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
        | ActionDefinition
        | FactionDefinition
        | RegionDefinition
        | PlaceDefinition
    ),
    Field(discriminator="family"),
]


class ErrorResponse(BaseModel):
    error: str
    message: Any


class QueryContractEnvelope(BaseModel):
    request_id: str
    catalog_revision: int
    status: str
    reason_code: str | None = None
    affected_definition_ids: list[str] = Field(default_factory=list)
    payload: Any


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
_PAYLOAD_FILTER_PREFIX = "pf_"


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


def _resolve_request_id(request: Request | None) -> str:
    if request is None:
        return uuid4().hex
    return request.headers.get("x-request-id") or uuid4().hex


def _serialize_validation_error(exc: ValidationError) -> dict[str, Any]:
    field_errors: dict[str, list[dict[str, str]]] = {}

    for error in exc.errors():
        raw_loc = error.get("loc", ())
        if isinstance(raw_loc, (list, tuple)):
            path_parts = tuple(raw_loc)
        else:
            path_parts = (raw_loc,)

        field_path = ".".join(
            str(part) for part in path_parts if part is not None) or "__root__"
        field_errors.setdefault(field_path, []).append(
            {
                "type": str(error.get("type", "validation_error")),
                "msg": str(error.get("msg", "Invalid value.")),
            }
        )

    return {
        "summary": str(exc),
        "field_errors": field_errors,
    }


def _domain_exception_parts(exc: Exception) -> tuple[int, str, Any]:
    if isinstance(exc, ValidationError):
        return (
            status.HTTP_400_BAD_REQUEST,
            CompendiumErrorCode.VALIDATION_FAILED.value,
            _serialize_validation_error(exc),
        )

    if isinstance(exc, ContentLifecycleError):
        code = CompendiumErrorCode.INVALID_LIFECYCLE_TRANSITION.value
        return (
            status.HTTP_409_CONFLICT,
            code,
            _strip_code_prefix(str(exc), code=code),
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

        return (
            status_code,
            code,
            _strip_code_prefix(str(exc), code=code),
        )

    return (
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "INTERNAL_ERROR",
        "Unhandled compendium error.",
    )


def _map_query_contract_exception(
    *,
    exc: Exception,
    request_id: str,
    catalog_revision: int,
) -> HTTPException:
    status_code, reason_code, message = _domain_exception_parts(exc)
    outcome_status = "error" if status_code >= 500 else "denied"

    return HTTPException(
        status_code=status_code,
        detail=QueryContractEnvelope(
            request_id=request_id,
            catalog_revision=catalog_revision,
            status=outcome_status,
            reason_code=reason_code,
            affected_definition_ids=[],
            payload={"message": message},
        ).model_dump(),
    )


def _map_domain_exception(exc: Exception) -> HTTPException:
    if isinstance(exc, HTTPException):
        return exc

    status_code, reason_code, message = _domain_exception_parts(exc)
    return HTTPException(
        status_code=status_code,
        detail=ErrorResponse(
            error=reason_code,
            message=message,
        ).model_dump(),
    )


def _extract_payload_filters(request: Request) -> dict[str, str]:
    payload_filters: dict[str, str] = {}
    for key, value in request.query_params.multi_items():
        if not key.startswith(_PAYLOAD_FILTER_PREFIX):
            continue
        filter_key = key[len(_PAYLOAD_FILTER_PREFIX):].strip()
        if not filter_key:
            continue
        value_text = value.strip()
        if not value_text:
            continue
        payload_filters[filter_key] = value_text
    return payload_filters


def _validate_payload_filters(
    *,
    family: DefinitionFamily | None,
    payload_filters: dict[str, str],
) -> None:
    if not payload_filters:
        return

    if family is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error=CompendiumErrorCode.VALIDATION_FAILED.value,
                message="Payload filters require an explicit family query parameter.",
            ).model_dump(),
        )

    allowed = set(FAMILY_PAYLOAD_FILTER_KEYS.get(family, ()))
    unsupported = sorted(key for key in payload_filters if key not in allowed)
    if unsupported:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error=CompendiumErrorCode.VALIDATION_FAILED.value,
                message=(
                    f"Unsupported payload filters for family '{family.value}': "
                    f"{', '.join(unsupported)}"
                ),
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


# ---------------------------------------------------------------------------
# V05-06: Search & Link Resolution Endpoints
# ---------------------------------------------------------------------------


@router.get("/search")
async def search_definitions(
    request: Request,
    q: str | None = Query(default=None, description="Full-text search term"),
    family: DefinitionFamily | None = Query(default=None),
    lifecycle_state: LifecycleState | None = Query(default=None),
    pack_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    include_contract: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    """Search the denormalized index — does NOT query the definitions table."""
    try:
        payload_filters = _extract_payload_filters(request)
        _validate_payload_filters(
            family=family, payload_filters=payload_filters)

        uow = CompendiumUnitOfWork(db)
        async with uow:
            states = [lifecycle_state.value] if lifecycle_state else None
            results = await uow.search_index.search(
                query_text=q,
                family=family.value if family else None,
                lifecycle_states=states,
                pack_id=pack_id,
                payload_filters=payload_filters or None,
                limit=limit,
                offset=offset,
            )

            if not include_contract:
                return results

            revision = await uow.search_index.get_catalog_revision(pack_id=pack_id)
            return QueryContractEnvelope(
                request_id=_resolve_request_id(request),
                catalog_revision=revision,
                status="resolved",
                affected_definition_ids=[doc.definition_id for doc in results],
                payload=results,
            )
    except Exception as exc:
        raise _map_domain_exception(exc) from exc


@router.get("/definitions/{definition_id}/links")
async def get_definition_links(
    definition_id: str,
    request: Request,
    include_contract: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    """Resolve forward and reverse links for a definition."""
    try:
        resolver = LinkedEntryResolutionService()
        uow = CompendiumUnitOfWork(db)
        revision = 0
        async with uow:
            forward_tree = await resolver.resolve_forward_links(definition_id, uow)
            reverse_links = await resolver.resolve_reverse_links(definition_id, uow)
            if include_contract:
                revision = await uow.search_index.get_catalog_revision()

        payload = {
            "definition_id": definition_id,
            "forward_links": [
                {
                    "link_id": link.link_id,
                    "source_id": link.source_id,
                    "target_id": link.target_id,
                    "relation_kind": link.relation_kind,
                    "status": link.status.value,
                    "target_name": link.target_name,
                    "target_family": link.target_family,
                }
                for link in forward_tree.links
            ],
            "reverse_links": [
                {
                    "link_id": link.link_id,
                    "source_id": link.source_id,
                    "target_id": link.target_id,
                    "relation_kind": link.relation_kind,
                    "status": link.status.value,
                    "target_name": link.target_name,
                    "target_family": link.target_family,
                }
                for link in reverse_links
            ],
            "broken_links": forward_tree.broken_links,
            "cycle_detected": forward_tree.cycle_detected,
        }

        if not include_contract:
            return payload

        affected_ids = [definition_id]
        affected_ids.extend(link.target_id for link in forward_tree.links)
        return QueryContractEnvelope(
            request_id=_resolve_request_id(request),
            catalog_revision=revision,
            status="resolved",
            affected_definition_ids=list(dict.fromkeys(affected_ids)),
            payload=payload,
        )
    except Exception as exc:
        raise _map_domain_exception(exc) from exc


@router.get("/definitions/{definition_id}/replacement-chain")
async def get_replacement_chain(
    definition_id: str,
    request: Request,
    include_contract: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    """Walk the replacement chain from a definition to its terminal node."""
    try:
        resolver = LinkedEntryResolutionService()
        uow = CompendiumUnitOfWork(db)
        revision = 0
        async with uow:
            chain = await resolver.resolve_replacement_chain(definition_id, uow)
            if include_contract:
                revision = await uow.search_index.get_catalog_revision()

        payload = {
            "definition_id": definition_id,
            "chain": chain,
            "terminal_id": chain[-1] if chain else definition_id,
        }

        if not include_contract:
            return payload

        return QueryContractEnvelope(
            request_id=_resolve_request_id(request),
            catalog_revision=revision,
            status="resolved",
            affected_definition_ids=chain or [definition_id],
            payload=payload,
        )
    except GraphCycleError as exc:
        if include_contract:
            raise _map_query_contract_exception(
                exc=exc,
                request_id=_resolve_request_id(request),
                catalog_revision=0,
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                error=CompendiumErrorCode.GRAPH_CYCLE_DETECTED.value,
                message=str(exc),
            ).model_dump(),
        ) from exc
    except Exception as exc:
        if include_contract:
            raise _map_query_contract_exception(
                exc=exc,
                request_id=_resolve_request_id(request),
                catalog_revision=0,
            ) from exc
        raise _map_domain_exception(exc) from exc
