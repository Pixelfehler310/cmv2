from __future__ import annotations
__production_status__ = "gold"

import logging

from src.core.sessions.manager import SessionManager
from src.core.ws_dispatcher import session_manager
from src.core.ws_protocol import Visibility, WsOutbound
from src.systems.dnd5e.content.application.services import ContentMutationEvent

logger = logging.getLogger(__name__)

_LIFECYCLE_EVENT_NAME_MAP: dict[str, str] = {
    "definition_published": "DefinitionPublished",
    "definition_archived": "DefinitionArchived",
    "definition_restored": "DefinitionRestored",
    "definition_superseded": "DefinitionSuperseded",
}


class ContentStreamWsHandler:
    """Broadcasts compendium lifecycle mutations into active campaign WS rooms."""

    def __init__(self, manager: SessionManager | None = None):
        self._manager = manager or session_manager
        self._last_catalog_revision_by_campaign: dict[str, int] = {}

    async def publish_mutation_event(self, event: ContentMutationEvent) -> None:
        lifecycle_event = _LIFECYCLE_EVENT_NAME_MAP.get(event.event_type)
        if lifecycle_event is not None:
            await self.emit_lifecycle_event(
                event_type=lifecycle_event,
                definition_id=event.definition_id,
                pack_id=event.pack_id,
                replacement_target_id=event.replacement_target_id,
                request_id=event.request_id,
                campaign_id=event.campaign_id,
            )

        if event.catalog_revision is not None:
            await self._emit_projection_events(event)

    async def _emit_projection_events(self, event: ContentMutationEvent) -> None:
        if event.campaign_id is not None:
            await self._emit_projection_for_campaign(event.campaign_id, event)
            return

        for active_campaign_id in self._manager.list_campaign_ids():
            await self._emit_projection_for_campaign(active_campaign_id, event)

    async def _emit_projection_for_campaign(
        self,
        campaign_id: str,
        event: ContentMutationEvent,
    ) -> None:
        revision = event.catalog_revision
        if revision is None:
            return

        previous = self._last_catalog_revision_by_campaign.get(campaign_id, 0)
        if revision > previous + 1 and previous > 0:
            await self.emit_invalidation_required(
                campaign_id=campaign_id,
                request_id=event.request_id,
                current_revision=previous,
                target_revision=revision,
                affected_definition_ids=event.affected_definition_ids or [event.definition_id],
            )

        await self.emit_projection_updated(
            campaign_id=campaign_id,
            request_id=event.request_id,
            catalog_revision=revision,
            affected_definition_ids=event.affected_definition_ids or [event.definition_id],
        )
        self._last_catalog_revision_by_campaign[campaign_id] = max(previous, revision)

    async def emit_lifecycle_event(
        self,
        *,
        event_type: str,
        definition_id: str,
        pack_id: str | None,
        request_id: str | None,
        replacement_target_id: str | None = None,
        campaign_id: str | None = None,
    ) -> None:
        outbound = WsOutbound(
            type="content_lifecycle_event",
            request_id=request_id,
            payload={
                "event_type": event_type,
                "definition_id": definition_id,
                "pack_id": pack_id,
                "replacement_target_id": replacement_target_id,
            },
            visibility=Visibility.ALL,
        )

        if campaign_id is not None:
            await self._manager.broadcast(campaign_id, outbound)
            return

        for active_campaign_id in self._manager.list_campaign_ids():
            try:
                await self._manager.broadcast(active_campaign_id, outbound)
            except Exception:
                logger.exception(
                    "Failed to broadcast content lifecycle event to campaign %s",
                    active_campaign_id,
                )

    async def emit_projection_updated(
        self,
        *,
        campaign_id: str,
        request_id: str | None,
        catalog_revision: int,
        affected_definition_ids: list[str],
    ) -> None:
        outbound = WsOutbound(
            type="content_projection_updated",
            request_id=request_id,
            payload={
                "catalog_revision": catalog_revision,
                "affected_definition_ids": affected_definition_ids,
            },
            visibility=Visibility.ALL,
        )
        await self._manager.broadcast(campaign_id, outbound)

    async def emit_invalidation_required(
        self,
        *,
        campaign_id: str,
        request_id: str | None,
        current_revision: int,
        target_revision: int,
        affected_definition_ids: list[str],
    ) -> None:
        outbound = WsOutbound(
            type="content_invalidation_required",
            request_id=request_id,
            payload={
                "current_revision": current_revision,
                "target_revision": target_revision,
                "affected_definition_ids": affected_definition_ids,
            },
            visibility=Visibility.ALL,
        )
        await self._manager.broadcast(campaign_id, outbound)
