# Test Plan: CORE-04 Session and Event Envelopes

## Unit Targets
1. Command envelope validation.
2. Final result envelope emission.
3. Denied and error terminal response behavior.

## Invariants
1. Every command has `request_id`.
2. Every command returns terminal status.
3. Denials are explicit and machine-readable.

## Edge Cases
1. Missing `request_id`.
2. Unknown `command_type`.
3. Event without revision metadata where required.

## Expected Results
1. Invalid command envelopes are denied.
2. Silent no-response behavior is forbidden.
3. Projection-affecting events include revision metadata.
