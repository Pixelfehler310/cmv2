# Changelog

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
