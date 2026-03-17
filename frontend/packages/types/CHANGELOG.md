# Changelog

## 0.0.3 - 2026-03-17

Contract target: data-driven foundations (PR-1).

### Added canonical domain contracts

- `ActionDefinitionContract`
- `AbilityBindingContract`
- `EffectDefinitionContract`
- `EffectInstanceContract`
- `ContentPackContract`

### Added effect and AoE denial taxonomy codes

- `effect_not_found`
- `target_immune`
- `target_invalid`
- `concentration_conflict`
- `stacking_limit_reached`
- `invalid_duration`
- `unsupported_effect_operation`
- `invalid_template_origin`
- `invalid_template_direction`
- `template_out_of_range`
- `no_resolved_targets`
- `target_not_in_template`
- `target_no_longer_eligible`
- `line_of_effect_blocked`

### Notes

- This release is contract-only and does not change resolver runtime behavior.

## 0.0.2 - 2026-03-17

Contract target: `ws-combat-v2` (Stage E hardening sync).

### Added inbound command-like contracts

- `request_executable_actions`
- `request_move_preview`
- `request_attack_preview`

### Added outbound event contracts

- `executable_actions_snapshot`
- `movement_preview`
- `attack_preview`

### Added payload contracts

- `ExecutableActionPayload`
- `ExecutableActionsSnapshotPayload`
- `MovementPreviewPayload`
- `AttackPreviewPayload`
- `AttackTemplateProjection`

### Notes

- Command-like envelopes continue to require `request_id`.
- Stage E alignment: backend docs, acceptance matrix, and frontend type package are synchronized.
