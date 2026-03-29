# Test Plan: DND5E-03 Action Mechanics

## Unit Targets
1. `ActionOperationSpec` payload discrimination.
2. `ResultReference` resolution and dependency ordering.
3. Modifier spec validation.

## Invariants
1. Every operation has stable `operation_id`.
2. Piped references resolve only to valid source operation outputs.
3. Unsupported `operation_type` values are denied.

## Edge Cases
1. Reference to unknown source operation.
2. Circular result piping dependency.
3. Payload operation type does not match discriminator.

## Expected Results
1. Invalid payloads fail with `VALIDATION_FAILED`.
2. Invalid graph dependencies fail before execution.
