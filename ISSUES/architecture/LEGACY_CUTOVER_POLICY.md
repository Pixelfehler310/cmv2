# Legacy Cutover Policy (AI Workflow)

This policy defines how AI and human contributors must handle legacy code during implementation.

## Intent

1. Legacy prototype code is considered superseded unless the task explicitly requests compatibility.
2. Delivery favors direct replacement and clean cutover in production paths.
3. Compatibility layers are exceptions, not defaults.

## Default Mode: Cutover

1. Do not add adapters, shims, bridge layers, or fallback paths to preserve legacy behavior.
2. Do not keep dual-write or dual-read paths unless explicitly requested.
3. Do not extend legacy modules when a production path can be implemented directly.
4. If a legacy dependency blocks implementation, prioritize in-scope dependency removal over compatibility wrapping.

## Exception Mode: Compatibility (Explicit Only)

Compatibility is allowed only when the user explicitly requests one of the following:

1. Backward compatibility with a specific legacy endpoint or module.
2. Staged rollout requiring temporary dual-path support.
3. Data migration period with documented rollback needs.

When compatibility mode is approved, the implementation must include:

1. Scope-limited compatibility path.
2. Removal plan with owner and deadline.
3. Tests that distinguish temporary compatibility behavior from target behavior.

## Mandatory Pre-Implementation Gate

Before coding starts, implementation notes must state:

1. Source of truth production path for this task.
2. Legacy path that will be bypassed or removed.
3. Explicit list of intentionally breaking legacy behaviors.
4. Confirmation that no adapter/fallback is added by default.

## PR Checklist (Required)

1. No new imports from legacy modules unless explicitly approved in task scope.
2. No adapter/fallback/shim paths introduced.
3. No dual behavior maintained unless explicitly approved.
4. Tests validate target contract behavior, not deprecated legacy semantics.
5. If exception mode is used: removal issue and cutoff date are documented.

## Enforcement Keywords

During review, treat these as red flags unless exception mode is active:

1. fallback
2. adapter
3. shim
4. bridge
5. compatibility mode
6. dual-write
7. dual-read

## References

1. `ISSUES/architecture/HOW_TO_PLAN.md`
2. `.github/copilot-instructions.md`
3. `ISSUES/architecture/APPROVAL_GATE_PROCEDURE.md`
