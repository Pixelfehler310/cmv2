from __future__ import annotations

from .invariants import CompendiumErrorCode


class CompendiumDomainError(ValueError):
    def __init__(self, code: CompendiumErrorCode, message: str):
        self.code = code
        super().__init__(f"{code.value}: {message}")


class ContentPackNotFoundError(CompendiumDomainError):
    def __init__(self, pack_id: str):
        super().__init__(
            CompendiumErrorCode.PACK_NOT_FOUND,
            f"Content pack '{pack_id}' does not exist.",
        )


class DefinitionNotFoundError(CompendiumDomainError):
    def __init__(self, definition_id: str):
        super().__init__(
            CompendiumErrorCode.DEFINITION_NOT_FOUND,
            f"Definition '{definition_id}' was not found.",
        )


class DuplicateDefinitionIdError(CompendiumDomainError):
    def __init__(self, definition_id: str):
        super().__init__(
            CompendiumErrorCode.DEFINITION_ID_CONFLICT,
            f"Definition id '{definition_id}' already exists.",
        )


class DuplicateDefinitionSlugError(CompendiumDomainError):
    def __init__(self, *, pack_id: str, family: str, slug: str):
        super().__init__(
            CompendiumErrorCode.DUPLICATE_SLUG,
            (
                "Duplicate slug in pack/family namespace: "
                f"pack_id='{pack_id}', family='{family}', slug='{slug}'."
            ),
        )


class VersionMismatchError(CompendiumDomainError):
    def __init__(self, *, expected: int, actual: int):
        super().__init__(
            CompendiumErrorCode.VERSION_MISMATCH,
            f"Expected content_version={expected}, actual={actual}.",
        )


class ImmutableDefinitionError(CompendiumDomainError):
    def __init__(self, *, lifecycle_state: str):
        super().__init__(
            CompendiumErrorCode.INVALID_LIFECYCLE_TRANSITION,
            f"Definition is immutable in lifecycle_state='{lifecycle_state}'.",
        )


class InvalidReplacementTargetError(CompendiumDomainError):
    def __init__(self, message: str):
        super().__init__(CompendiumErrorCode.INVALID_REPLACEMENT_TARGET, message)


class LinkedTargetInUseError(CompendiumDomainError):
    def __init__(self, *, definition_id: str, reference_count: int):
        super().__init__(
            CompendiumErrorCode.LINKED_TARGET_IN_USE,
            (
                f"Definition '{definition_id}' is still referenced by "
                f"{reference_count} linked entries."
            ),
        )


class LinkedTargetNotFoundError(CompendiumDomainError):
    def __init__(self, target_definition_id: str):
        super().__init__(
            CompendiumErrorCode.LINKED_TARGET_NOT_FOUND,
            f"Linked target '{target_definition_id}' does not exist.",
        )


class ReplacementCycleError(CompendiumDomainError):
    def __init__(self, message: str):
        super().__init__(CompendiumErrorCode.CYCLE_DETECTED, message)
