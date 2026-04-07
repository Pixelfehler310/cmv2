# Module Specifications

This directory holds pre-implementation module annex specifications for active and implemented backend modules.

## Purpose

1. Capture near-implementation architecture detail before coding.
2. Keep methods, constraints, context objects, and recovery behavior explicit.
3. Provide module-by-module approval evidence for freeze gates.

## Required Inputs per Module

1. Class model coverage (attributes and primary methods).
2. Sequence coverage for resolved and denied or recovery paths.
3. Activity coverage for decision and orchestration flow.
4. Context object catalog with ownership and mutability rules.
5. Constraint and reason-code mapping.

## Completion and Approval

Use:

1. `ISSUES/architecture/APPROVAL_GATE_PROCEDURE.md`
2. `ISSUES/architecture/01_contracts/APPROVAL_LOG.md`
3. `ISSUES/architecture/01_contracts/MODULE_DETAIL_SCORECARD_TEMPLATE.md`
