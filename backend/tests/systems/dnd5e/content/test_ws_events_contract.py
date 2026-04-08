from __future__ import annotations

from typing import Any

import pytest

from src.systems.dnd5e.content.api.ws_events import ContentStreamWsHandler
from src.systems.dnd5e.content.application.services import ContentMutationEvent


class FakeSessionManager:
    def __init__(self) -> None:
        self.broadcasts: list[tuple[str, Any]] = []

    async def broadcast(self, campaign_id: str, outbound) -> None:
        self.broadcasts.append((campaign_id, outbound))

    def list_campaign_ids(self) -> list[str]:
        return ["campaign-a"]


@pytest.mark.asyncio
async def test_publish_mutation_emits_projection_updated_with_revision():
    manager = FakeSessionManager()
    handler = ContentStreamWsHandler(manager=manager)  # type: ignore[arg-type]

    await handler.publish_mutation_event(
        ContentMutationEvent(
            event_type="definition_published",
            definition_id="def-1",
            family="monster",
            lifecycle_state="published",
            content_version=2,
            campaign_id="campaign-a",
            request_id="req-1",
            catalog_revision=10,
            affected_definition_ids=["def-1"],
        )
    )

    projection_events = [
        outbound
        for campaign_id, outbound in manager.broadcasts
        if campaign_id == "campaign-a" and outbound.type == "content_projection_updated"
    ]
    assert len(projection_events) == 1
    assert projection_events[0].request_id == "req-1"
    assert projection_events[0].payload["catalog_revision"] == 10
    assert projection_events[0].payload["affected_definition_ids"] == ["def-1"]


@pytest.mark.asyncio
async def test_revision_gap_emits_invalidation_required():
    manager = FakeSessionManager()
    handler = ContentStreamWsHandler(manager=manager)  # type: ignore[arg-type]

    await handler.publish_mutation_event(
        ContentMutationEvent(
            event_type="definition_published",
            definition_id="def-1",
            family="monster",
            lifecycle_state="published",
            content_version=2,
            campaign_id="campaign-a",
            catalog_revision=10,
            affected_definition_ids=["def-1"],
        )
    )
    await handler.publish_mutation_event(
        ContentMutationEvent(
            event_type="definition_updated",
            definition_id="def-2",
            family="monster",
            lifecycle_state="published",
            content_version=3,
            campaign_id="campaign-a",
            catalog_revision=13,
            affected_definition_ids=["def-2"],
        )
    )

    invalidation_events = [
        outbound
        for campaign_id, outbound in manager.broadcasts
        if campaign_id == "campaign-a" and outbound.type == "content_invalidation_required"
    ]
    assert len(invalidation_events) == 1
    assert invalidation_events[0].payload["current_revision"] == 10
    assert invalidation_events[0].payload["target_revision"] == 13
    assert invalidation_events[0].payload["affected_definition_ids"] == ["def-2"]


@pytest.mark.asyncio
async def test_stale_revision_event_is_ignored():
    manager = FakeSessionManager()
    handler = ContentStreamWsHandler(manager=manager)  # type: ignore[arg-type]

    await handler.publish_mutation_event(
        ContentMutationEvent(
            event_type="definition_published",
            definition_id="def-new",
            family="monster",
            lifecycle_state="published",
            content_version=2,
            campaign_id="campaign-a",
            catalog_revision=10,
            affected_definition_ids=["def-new"],
        )
    )

    before_count = len(manager.broadcasts)

    await handler.publish_mutation_event(
        ContentMutationEvent(
            event_type="definition_updated",
            definition_id="def-old",
            family="monster",
            lifecycle_state="published",
            content_version=3,
            campaign_id="campaign-a",
            catalog_revision=9,
            affected_definition_ids=["def-old"],
        )
    )

    after_count = len(manager.broadcasts)
    assert after_count == before_count
