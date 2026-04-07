# Module Annex: assets

## Scope

Asset registration, linkage, ownership policy, and archival lifecycle.

## Primary Classes

1. `AssetDefinition` for canonical media metadata and lifecycle.
2. `AssetRegistry` for registration and retrieval orchestration.
3. `AssetLinkage` for scene and combat-state linkage records.
4. `AssetOwnershipPolicy` for read-modify-share permission control.
5. `AssetLifecycleManager` for publish-archive-retention transitions.
6. `AssetMetadata` and `AccessControl` as immutable value models.

## Externally Callable Methods (10+)

1. `register_asset(asset_def, owner_user_id, campaign_id=None)`
2. `publish_asset(asset_id, user_id)`
3. `archive_asset(asset_id, user_id, reason)`
4. `link_asset_to_scene(asset_id, scene_id, user_id, layer_index)`
5. `unlink_asset_from_scene(linkage_id, scene_id, user_id)`
6. `grant_access(asset_id, grantee_user_id, access_type, grantor_user_id)`
7. `revoke_access(asset_id, user_id, grantor_user_id)`
8. `get_asset_by_linkage(linkage_id, user_id)`
9. `list_assets_for_scene(scene_id, user_id)`
10. `bulk_archive_by_campaign(campaign_id, user_id, reason)`
11. `validate_asset_metadata(asset_def)`
12. `schedule_asset_purge(asset_id, archived_at, retention_days)`

## Critical Flows

1. Asset registration and owner policy initialization.
2. Asset publish transition and index availability.
3. Scene linkage and unlink idempotent cleanup.
4. Manual and bulk archival with retention-scheduled purge.

## Context Objects

1. `AssetRegistration` context for registry output and event emission.
2. `AssetLinkageContext` for scene-layer binding metadata.
3. `AccessControlContext` for explicit permission grant and revoke actions.
4. `AssetArchivalContext` for retention and cleanup workflow.
5. `AssetMutationContext` for request correlation and ownership validation.

Mutability:

1. Registration and linkage contexts are immutable once emitted.
2. Access control records are mutable via explicit grant-revoke operations only.
3. Archival context is immutable and drives scheduled lifecycle completion.

## Constraints and Denial Mapping

Invariants:

1. Asset type and metadata shape must pass validation before registration.
2. Non-published assets cannot be linked for active rendering.
3. Layer index boundaries are enforced for scene composition.
4. Only owner or DM lane can archive or grant access.

Reason-code families:

1. `INVALID_ASSET_METADATA`
2. `ASSET_NOT_FOUND`
3. `ASSET_STATE_INVALID`
4. `INSUFFICIENT_PERMISSION`
5. `ASSET_NOT_PUBLISHED`
6. `LINKAGE_NOT_FOUND`
7. `ASSET_IN_USE`

## Recovery and Idempotency

1. Unlink and archival operations should be idempotent for already-terminal state.
2. Failed publish retries are valid after metadata correction.
3. Bulk archival should skip already archived assets safely.
4. Purge scheduling must preserve audit trail for archived assets.

## Traceability

1. Contracts: `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-05]_layer_ownership.md`.
2. Contracts: `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-04]_session_event_envelopes.md`.
3. Diagrams: `ISSUES/architecture/01_contracts/overview/MASTER_SYSTEM_CLASS_SPEC.mmd`.
4. Code anchors: `backend/src/common/` persistence patterns and `backend/src/schemas/` asset-related DTO surfaces.
