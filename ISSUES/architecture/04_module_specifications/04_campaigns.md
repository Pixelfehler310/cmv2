# Module Annex: campaigns

## Scope

Campaign identity, membership policy, lifecycle gates, and cross-campaign boundary enforcement.

## Primary Classes

1. `Campaign` aggregate root.
2. `CampaignMember` role and entitlement binding.
3. `CampaignRole` value enum for DM, player, spectator policy lanes.
4. `CampaignContextApplicationService` for context retrieval and mutation orchestration.
5. `CampaignContextResponse` read model for active scene and encounter pointer.
6. `AdminBypassContext` computed privilege overlay.

## Externally Callable Methods (10+)

1. `create_campaign(name, description, current_user)`
2. `get_campaigns(skip, limit, current_user, db)`
3. `get_campaign(campaign_id, current_user, db)`
4. `join_campaign(campaign_id, current_user, db)`
5. `delete_campaign(campaign_id, current_user, db)`
6. `get_campaign_context(campaign_id, current_user, db)`
7. `list_campaign_scenes(campaign_id, current_user, db)`
8. `list_scene_encounters(campaign_id, scene_id, current_user, db)`
9. `select_campaign_context(campaign_id, request, current_user, db)`
10. `_resolve_member_or_raise(db, campaign_id, current_user)`
11. `_campaign_with_character_relations()`

## Critical Flows

1. Campaign creation with automatic DM enrollment.
2. Join campaign with idempotent already-member handling.
3. DM-only context selection for scene and encounter switching.
4. Campaign delete with cascade cleanup and role checks.

## Context Objects

1. `User` identity object from auth dependency.
2. `CampaignMember` entitlement state.
3. `CampaignContextResponse` scope projection.
4. `AsyncSession` transactional context.
5. `AdminBypass` decision context.

Mutability:

1. Membership role lane is immutable except explicit role mutation operations.
2. Active character pointer and context version are mutable under authorized operations.
3. Context responses are immutable output objects.

## Constraints and Denial Mapping

Invariants:

1. `(campaign_id, user_id)` membership pair must be unique.
2. Cross-campaign operations are always denied.
3. DM-only operations require DM role or admin override.
4. Context version increments on successful context selection.

Reason-code families:

1. `campaigns.permission.not_a_member`
2. `campaigns.permission.insufficient_role`
3. `campaigns.not_found.campaign`
4. `campaigns.not_found.scene`
5. `campaigns.not_found.encounter`
6. `campaigns.conflict.already_member`

## Recovery and Idempotency

1. Join flow is idempotent for already-existing membership.
2. Delete flow is deterministic (repeated delete becomes not-found).
3. Context selection retries must preserve request correlation.
4. Membership and context failures require explicit correction before retry.

## Traceability

1. Contracts: `ISSUES/architecture/01_contracts/campaign/ISSUE_[CONTRACT]_[CAM-01]_campaign_management_context.md`.
2. Contracts: `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-05]_layer_ownership.md`.
3. Diagrams: `ISSUES/architecture/01_contracts/overview/HORIZONTAL_CONTRACT_DETAIL_OVERVIEW.mmd`.
4. Code anchors: `backend/src/schemas/campaign.py`.
