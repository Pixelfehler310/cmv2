from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ..domain.errors import GraphCycleError
from ..domain.link_models import LinkedEntryReference, RelationKind
from ..infrastructure.unit_of_work import CompendiumUnitOfWork


class LinkStatus(str, Enum):
    RESOLVED = "resolved"
    BROKEN = "broken"


@dataclass(slots=True)
class ResolvedLink:
    """A single resolved link with its target status."""

    link_id: str
    source_id: str
    target_id: str
    relation_kind: str
    status: LinkStatus
    target_name: str | None = None
    target_family: str | None = None
    target_lifecycle_state: str | None = None


@dataclass(slots=True)
class ResolvedLinkTree:
    """Result of a full forward-link graph traversal from a root definition."""

    root_definition_id: str
    links: list[ResolvedLink] = field(default_factory=list)
    broken_links: list[str] = field(default_factory=list)
    cycle_detected: bool = False
    cycle_path: list[str] = field(default_factory=list)


class LinkedEntryResolutionService:
    """
    Recursive graph resolver for LinkedEntryReference traversal.

    This is the read-path complement to LinkedEntryIntegrityPolicy (write-path).
    It traverses the link graph without mutating any data, building resolved
    trees with cycle detection and broken-link marking.
    """

    MAX_TRAVERSAL_DEPTH = 50  # Safety limit against pathological graphs.

    async def resolve_forward_links(
        self,
        definition_id: str,
        uow: CompendiumUnitOfWork,
        *,
        max_depth: int | None = None,
    ) -> ResolvedLinkTree:
        """
        Traverse all forward LinkedEntryReferences from a root definition.

        Builds a result tree. If a cycle is detected, it is marked on the
        tree without raising — the caller decides how to handle it.
        Missing targets are marked as BROKEN rather than crashing.
        """
        depth_limit = max_depth or self.MAX_TRAVERSAL_DEPTH
        tree = ResolvedLinkTree(root_definition_id=definition_id)
        visited: set[str] = set()

        await self._traverse_forward(
            definition_id=definition_id,
            uow=uow,
            tree=tree,
            visited=visited,
            depth=0,
            depth_limit=depth_limit,
        )

        return tree

    async def resolve_reverse_links(
        self,
        definition_id: str,
        uow: CompendiumUnitOfWork,
    ) -> list[ResolvedLink]:
        """
        Find all definitions that link TO this definition (reverse lookup).
        """
        raw_links = await uow.links.list_by_target_definition_id(definition_id)
        results: list[ResolvedLink] = []

        for link in raw_links:
            source_def = await uow.definitions.get_by_id(link.source_definition_id)

            if source_def is None:
                results.append(
                    ResolvedLink(
                        link_id=link.id,
                        source_id=link.source_definition_id,
                        target_id=definition_id,
                        relation_kind=link.relation_kind.value,
                        status=LinkStatus.BROKEN,
                    )
                )
            else:
                results.append(
                    ResolvedLink(
                        link_id=link.id,
                        source_id=link.source_definition_id,
                        target_id=definition_id,
                        relation_kind=link.relation_kind.value,
                        status=LinkStatus.RESOLVED,
                        target_name=source_def.name,
                        target_family=source_def.family.value,
                        target_lifecycle_state=source_def.lifecycle_state.value,
                    )
                )

        return results

    async def resolve_replacement_chain(
        self,
        definition_id: str,
        uow: CompendiumUnitOfWork,
    ) -> list[str]:
        """
        Walk the replacement chain from a definition to its terminal node.

        Returns the ordered list of definition IDs in the chain.
        Raises GraphCycleError if a cycle is detected.
        """
        chain: list[str] = [definition_id]
        visited: set[str] = {definition_id}
        cursor: str | None = definition_id

        while cursor is not None:
            next_id = await uow.links.get_replacement_target(cursor)
            if next_id is None:
                break

            if next_id in visited:
                raise GraphCycleError(
                    definition_id=next_id,
                    visited_path=chain,
                )

            visited.add(next_id)
            chain.append(next_id)
            cursor = next_id

        return chain

    async def _traverse_forward(
        self,
        *,
        definition_id: str,
        uow: CompendiumUnitOfWork,
        tree: ResolvedLinkTree,
        visited: set[str],
        depth: int,
        depth_limit: int,
    ) -> None:
        """Recursive forward traversal with cycle detection and depth limiting."""
        if depth >= depth_limit:
            return

        if definition_id in visited:
            tree.cycle_detected = True
            tree.cycle_path = list(visited)
            return

        visited.add(definition_id)

        forward_links = await uow.links.list_by_source_definition_id(definition_id)

        for link in forward_links:
            target_def = await uow.definitions.get_by_id(link.target_definition_id)

            if target_def is None:
                # Broken link — target was deleted or doesn't exist
                tree.links.append(
                    ResolvedLink(
                        link_id=link.id,
                        source_id=link.source_definition_id,
                        target_id=link.target_definition_id,
                        relation_kind=link.relation_kind.value,
                        status=LinkStatus.BROKEN,
                    )
                )
                tree.broken_links.append(link.target_definition_id)
            else:
                tree.links.append(
                    ResolvedLink(
                        link_id=link.id,
                        source_id=link.source_definition_id,
                        target_id=link.target_definition_id,
                        relation_kind=link.relation_kind.value,
                        status=LinkStatus.RESOLVED,
                        target_name=target_def.name,
                        target_family=target_def.family.value,
                        target_lifecycle_state=target_def.lifecycle_state.value,
                    )
                )

                # Recurse into the target's forward links (non-replacement only)
                if link.relation_kind != RelationKind.REPLACEMENT:
                    await self._traverse_forward(
                        definition_id=link.target_definition_id,
                        uow=uow,
                        tree=tree,
                        visited=visited,
                        depth=depth + 1,
                        depth_limit=depth_limit,
                    )

        visited.discard(definition_id)
