from __future__ import annotations
__production_status__ = "gold"

from collections.abc import Awaitable, Callable

from ..domain.errors import (
    IllegalStateDependencyError,
    InvalidReplacementTargetError,
    LinkedTargetNotFoundError,
    ReplacementCycleError,
)
from ..domain.link_models import LinkedEntryReference, RelationKind, ResolveMode
from ..domain.primitives import DefinitionFamily, LifecycleState


class LinkedEntryIntegrityPolicy:
    """Validates linked-entry integrity constraints before persistence writes."""

    @staticmethod
    def validate_target_family(
        *,
        source_family: DefinitionFamily,
        target_family: DefinitionFamily,
        relation_kind: RelationKind,
    ) -> None:
        if (
            relation_kind == RelationKind.REPLACEMENT
            and source_family != target_family
        ):
            raise InvalidReplacementTargetError(
                "Replacement links require source and target to share the same family."
            )

    @staticmethod
    async def validate_required_targets_exist(
        *,
        links: list[LinkedEntryReference],
        target_lookup: Callable[[str], Awaitable[object | None]],
    ) -> None:
        for link in links:
            if not link.required:
                continue
            if link.resolve_mode != ResolveMode.STRICT:
                continue

            target = await target_lookup(link.target_definition_id)
            if target is None:
                raise LinkedTargetNotFoundError(link.target_definition_id)

    @staticmethod
    async def validate_replacement_cycle_safety(
        *,
        source_definition_id: str,
        replacement_target_id: str,
        replacement_target_lookup: Callable[[str], Awaitable[str | None]],
    ) -> None:
        visited: set[str] = set()
        cursor: str | None = replacement_target_id

        while cursor is not None:
            if cursor == source_definition_id:
                raise ReplacementCycleError(
                    "Replacement chain would create a cycle."
                )

            if cursor in visited:
                raise ReplacementCycleError(
                    "Existing replacement chain already contains a cycle."
                )

            visited.add(cursor)
            cursor = await replacement_target_lookup(cursor)

    @staticmethod
    async def validate_published_targets_only(
        *,
        links: list[LinkedEntryReference],
        target_lookup: Callable[[str], Awaitable[object | None]],
    ) -> None:
        """
        Ensures that all mandatory links point to PUBLISHED or ARCHIVED entries.
        Prevents 'Published -> Draft' dependency leaks.
        """
        for link in links:
            if not link.required:
                continue
            if link.resolve_mode != ResolveMode.STRICT:
                continue

            target: Any = await target_lookup(link.target_definition_id)
            if target is None:
                raise LinkedTargetNotFoundError(link.target_definition_id)

            if target.lifecycle_state == LifecycleState.DRAFT:
                raise IllegalStateDependencyError(
                    f"Published entity cannot depend on DRAFT target '{target.id}'."
                )
