from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..lib.content_models import ActionDefinitionRecord, AbilityBindingRecord, EffectDefinitionRecord
from ..schemas.contracts import ContentPack

ConflictPolicy = Literal["reject_conflict",
                         "overwrite_if_newer", "fork_namespace"]


@dataclass
class ImportSummary:
    discovered: int = 0
    inserted: int = 0
    updated: int = 0
    skipped_existing: int = 0
    failed: int = 0
    conflicts: int = 0
    forked: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "discovered": self.discovered,
            "inserted": self.inserted,
            "updated": self.updated,
            "skipped_existing": self.skipped_existing,
            "failed": self.failed,
            "conflicts": self.conflicts,
            "forked": self.forked,
        }


class ContentPackImporter:
    async def import_content_pack(
        self,
        session: AsyncSession,
        payload: dict[str, Any],
        conflict_policy: ConflictPolicy = "reject_conflict",
        namespace: str | None = None,
    ) -> dict[str, Any]:
        pack = ContentPack.model_validate(payload)
        semantic_errors = await self._validate_semantics(session, pack)
        if semantic_errors:
            return {
                "status": "failed",
                "pack_id": pack.pack_id,
                "error": "semantic_validation_failed",
                "semantic_errors": semantic_errors,
                "summary": {
                    "actions": ImportSummary(discovered=len(pack.actions)).to_dict(),
                    "abilities": ImportSummary(discovered=len(pack.abilities)).to_dict(),
                    "effects": ImportSummary(discovered=len(pack.effects)).to_dict(),
                },
            }

        action_summary = await self._import_actions(session, pack, conflict_policy, namespace)
        effect_summary = await self._import_effects(session, pack, conflict_policy, namespace)
        ability_summary = await self._import_abilities(session, pack, conflict_policy, namespace)

        await session.commit()

        failed = action_summary.failed + effect_summary.failed + ability_summary.failed
        status = "success" if failed == 0 else "partial_success"
        return {
            "status": status,
            "pack_id": pack.pack_id,
            "summary": {
                "actions": action_summary.to_dict(),
                "abilities": ability_summary.to_dict(),
                "effects": effect_summary.to_dict(),
            },
            "conflict_policy": conflict_policy,
        }

    async def _validate_semantics(self, session: AsyncSession, pack: ContentPack) -> list[str]:
        errors: list[str] = []

        pack_action_ids = {action.action_id for action in pack.actions}
        pack_effect_ids = {effect.effect_id for effect in pack.effects}

        for binding in pack.abilities:
            if not (binding.actor_template_id or binding.actor_id):
                errors.append(
                    f"ability:{binding.binding_id}:missing_actor_binding")
            if binding.action_id not in pack_action_ids:
                exists = await self._action_exists(session, pack.system, binding.action_id)
                if not exists:
                    errors.append(
                        f"ability:{binding.binding_id}:unknown_action:{binding.action_id}")

        for action in pack.actions:
            for idx, intent in enumerate(action.effect_intents):
                if not isinstance(intent, dict):
                    errors.append(
                        f"action:{action.action_id}:effect_intent:{idx}:must_be_object")
                    continue
                effect_id = intent.get("effect_id")
                if not effect_id:
                    continue
                if effect_id not in pack_effect_ids:
                    exists = await self._effect_exists(session, pack.system, effect_id)
                    if not exists:
                        errors.append(
                            f"action:{action.action_id}:unknown_effect:{effect_id}")

        return errors

    async def _action_exists(self, session: AsyncSession, system: str, action_id: str) -> bool:
        stmt = select(ActionDefinitionRecord).where(
            ActionDefinitionRecord.system == system,
            ActionDefinitionRecord.action_id == action_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def _effect_exists(self, session: AsyncSession, system: str, effect_id: str) -> bool:
        stmt = select(EffectDefinitionRecord).where(
            EffectDefinitionRecord.system == system,
            EffectDefinitionRecord.effect_id == effect_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def _import_actions(
        self,
        session: AsyncSession,
        pack: ContentPack,
        conflict_policy: ConflictPolicy,
        namespace: str | None,
    ) -> ImportSummary:
        summary = ImportSummary(discovered=len(pack.actions))
        for action in pack.actions:
            try:
                existing = await self._get_action(session, pack.system, action.action_id)
                if existing is None:
                    session.add(
                        ActionDefinitionRecord(
                            system=pack.system,
                            action_id=action.action_id,
                            name=action.name,
                            family=action.family,
                            action_type_cost=action.action_type_cost,
                            targeting_mode=action.targeting_mode,
                            range=action.range,
                            save_context=action.save_context,
                            attack_context=action.attack_context,
                            resource_costs=action.resource_costs,
                            effect_intents=action.effect_intents,
                            tags=action.tags,
                            source_ref=action.source_ref,
                            content_version=action.content_version,
                            enabled=action.enabled,
                            pack_id=pack.pack_id,
                            pack_version=pack.version,
                        )
                    )
                    summary.inserted += 1
                    continue

                resolved = await self._resolve_conflict(
                    session=session,
                    existing=existing,
                    incoming_version=action.content_version,
                    incoming_key=action.action_id,
                    system=pack.system,
                    conflict_policy=conflict_policy,
                    namespace=namespace or pack.pack_id,
                    table="action",
                )

                if resolved["state"] == "conflict":
                    summary.conflicts += 1
                    summary.skipped_existing += 1
                elif resolved["state"] == "skip":
                    summary.skipped_existing += 1
                elif resolved["state"] == "fork":
                    session.add(
                        ActionDefinitionRecord(
                            system=pack.system,
                            action_id=resolved["key"],
                            name=action.name,
                            family=action.family,
                            action_type_cost=action.action_type_cost,
                            targeting_mode=action.targeting_mode,
                            range=action.range,
                            save_context=action.save_context,
                            attack_context=action.attack_context,
                            resource_costs=action.resource_costs,
                            effect_intents=action.effect_intents,
                            tags=action.tags,
                            source_ref=action.source_ref,
                            content_version=action.content_version,
                            enabled=action.enabled,
                            pack_id=pack.pack_id,
                            pack_version=pack.version,
                        )
                    )
                    summary.forked += 1
                    summary.inserted += 1
                else:
                    existing.name = action.name
                    existing.family = action.family
                    existing.action_type_cost = action.action_type_cost
                    existing.targeting_mode = action.targeting_mode
                    existing.range = action.range
                    existing.save_context = action.save_context
                    existing.attack_context = action.attack_context
                    existing.resource_costs = action.resource_costs
                    existing.effect_intents = action.effect_intents
                    existing.tags = action.tags
                    existing.source_ref = action.source_ref
                    existing.content_version = action.content_version
                    existing.enabled = action.enabled
                    existing.pack_id = pack.pack_id
                    existing.pack_version = pack.version
                    summary.updated += 1
            except Exception:
                summary.failed += 1

        return summary

    async def _import_effects(
        self,
        session: AsyncSession,
        pack: ContentPack,
        conflict_policy: ConflictPolicy,
        namespace: str | None,
    ) -> ImportSummary:
        summary = ImportSummary(discovered=len(pack.effects))
        for effect in pack.effects:
            try:
                existing = await self._get_effect(session, pack.system, effect.effect_id)
                incoming_version = str(effect.metadata.get(
                    "content_version", pack.version))
                if existing is None:
                    session.add(
                        EffectDefinitionRecord(
                            system=pack.system,
                            effect_id=effect.effect_id,
                            name=effect.name,
                            family=effect.family,
                            duration=effect.duration.model_dump(mode="json"),
                            stacking=effect.stacking.model_dump(mode="json"),
                            tags=effect.tags,
                            modifiers=[m.model_dump(mode="json")
                                       for m in effect.modifiers],
                            grants_conditions=effect.grants_conditions,
                            periodic=[p.model_dump(mode="json")
                                      for p in effect.periodic],
                            removal_triggers=[r.model_dump(
                                mode="json") for r in effect.removal_triggers],
                            metadata_json=effect.metadata,
                            content_version=incoming_version,
                            enabled=True,
                            pack_id=pack.pack_id,
                            pack_version=pack.version,
                        )
                    )
                    summary.inserted += 1
                    continue

                resolved = await self._resolve_conflict(
                    session=session,
                    existing=existing,
                    incoming_version=incoming_version,
                    incoming_key=effect.effect_id,
                    system=pack.system,
                    conflict_policy=conflict_policy,
                    namespace=namespace or pack.pack_id,
                    table="effect",
                )

                if resolved["state"] == "conflict":
                    summary.conflicts += 1
                    summary.skipped_existing += 1
                elif resolved["state"] == "skip":
                    summary.skipped_existing += 1
                elif resolved["state"] == "fork":
                    session.add(
                        EffectDefinitionRecord(
                            system=pack.system,
                            effect_id=resolved["key"],
                            name=effect.name,
                            family=effect.family,
                            duration=effect.duration.model_dump(mode="json"),
                            stacking=effect.stacking.model_dump(mode="json"),
                            tags=effect.tags,
                            modifiers=[m.model_dump(mode="json")
                                       for m in effect.modifiers],
                            grants_conditions=effect.grants_conditions,
                            periodic=[p.model_dump(mode="json")
                                      for p in effect.periodic],
                            removal_triggers=[r.model_dump(
                                mode="json") for r in effect.removal_triggers],
                            metadata_json=effect.metadata,
                            content_version=incoming_version,
                            enabled=True,
                            pack_id=pack.pack_id,
                            pack_version=pack.version,
                        )
                    )
                    summary.forked += 1
                    summary.inserted += 1
                else:
                    existing.name = effect.name
                    existing.family = effect.family
                    existing.duration = effect.duration.model_dump(mode="json")
                    existing.stacking = effect.stacking.model_dump(mode="json")
                    existing.tags = effect.tags
                    existing.modifiers = [m.model_dump(
                        mode="json") for m in effect.modifiers]
                    existing.grants_conditions = effect.grants_conditions
                    existing.periodic = [p.model_dump(
                        mode="json") for p in effect.periodic]
                    existing.removal_triggers = [r.model_dump(
                        mode="json") for r in effect.removal_triggers]
                    existing.metadata_json = effect.metadata
                    existing.content_version = incoming_version
                    existing.pack_id = pack.pack_id
                    existing.pack_version = pack.version
                    summary.updated += 1
            except Exception:
                summary.failed += 1

        return summary

    async def _import_abilities(
        self,
        session: AsyncSession,
        pack: ContentPack,
        conflict_policy: ConflictPolicy,
        namespace: str | None,
    ) -> ImportSummary:
        summary = ImportSummary(discovered=len(pack.abilities))
        for binding in pack.abilities:
            try:
                existing = await self._get_binding(session, pack.system, binding.binding_id)
                if existing is None:
                    session.add(
                        AbilityBindingRecord(
                            system=pack.system,
                            binding_id=binding.binding_id,
                            action_id=binding.action_id,
                            actor_template_id=binding.actor_template_id,
                            actor_id=binding.actor_id,
                            unlock_conditions=binding.unlock_conditions,
                            override_payload=binding.override_payload,
                            pack_id=pack.pack_id,
                            pack_version=pack.version,
                        )
                    )
                    summary.inserted += 1
                    continue

                resolved = await self._resolve_conflict(
                    session=session,
                    existing=existing,
                    incoming_version=pack.version,
                    incoming_key=binding.binding_id,
                    system=pack.system,
                    conflict_policy=conflict_policy,
                    namespace=namespace or pack.pack_id,
                    table="ability",
                )

                if resolved["state"] == "conflict":
                    summary.conflicts += 1
                    summary.skipped_existing += 1
                elif resolved["state"] == "skip":
                    summary.skipped_existing += 1
                elif resolved["state"] == "fork":
                    session.add(
                        AbilityBindingRecord(
                            system=pack.system,
                            binding_id=resolved["key"],
                            action_id=binding.action_id,
                            actor_template_id=binding.actor_template_id,
                            actor_id=binding.actor_id,
                            unlock_conditions=binding.unlock_conditions,
                            override_payload=binding.override_payload,
                            pack_id=pack.pack_id,
                            pack_version=pack.version,
                        )
                    )
                    summary.forked += 1
                    summary.inserted += 1
                else:
                    existing.action_id = binding.action_id
                    existing.actor_template_id = binding.actor_template_id
                    existing.actor_id = binding.actor_id
                    existing.unlock_conditions = binding.unlock_conditions
                    existing.override_payload = binding.override_payload
                    existing.pack_id = pack.pack_id
                    existing.pack_version = pack.version
                    summary.updated += 1
            except Exception:
                summary.failed += 1

        return summary

    async def _resolve_conflict(
        self,
        session: AsyncSession,
        existing: Any,
        incoming_version: str,
        incoming_key: str,
        system: str,
        conflict_policy: ConflictPolicy,
        namespace: str,
        table: Literal["action", "ability", "effect"],
    ) -> dict[str, str]:
        if conflict_policy == "reject_conflict":
            return {"state": "conflict", "key": incoming_key}

        if conflict_policy == "overwrite_if_newer":
            if self._version_is_newer(incoming_version, str(getattr(existing, "content_version", "0"))):
                return {"state": "update", "key": incoming_key}
            return {"state": "skip", "key": incoming_key}

        fork_key = await self._next_fork_key(session, system, namespace, incoming_key, table)
        return {"state": "fork", "key": fork_key}

    async def _next_fork_key(
        self,
        session: AsyncSession,
        system: str,
        namespace: str,
        source_key: str,
        table: Literal["action", "ability", "effect"],
    ) -> str:
        cleaned_namespace = re.sub(
            r"[^a-zA-Z0-9_-]", "_", namespace).strip("_") or "fork"
        candidate = f"{cleaned_namespace}::{source_key}"
        index = 1

        while True:
            if table == "action":
                exists = await self._action_exists(session, system, candidate)
            elif table == "effect":
                exists = await self._effect_exists(session, system, candidate)
            else:
                stmt = select(AbilityBindingRecord).where(
                    AbilityBindingRecord.system == system,
                    AbilityBindingRecord.binding_id == candidate,
                )
                result = await session.execute(stmt)
                exists = result.scalar_one_or_none() is not None

            if not exists:
                return candidate

            index += 1
            candidate = f"{cleaned_namespace}::{source_key}::{index}"

    async def _get_action(self, session: AsyncSession, system: str, action_id: str) -> ActionDefinitionRecord | None:
        stmt = select(ActionDefinitionRecord).where(
            ActionDefinitionRecord.system == system,
            ActionDefinitionRecord.action_id == action_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_binding(self, session: AsyncSession, system: str, binding_id: str) -> AbilityBindingRecord | None:
        stmt = select(AbilityBindingRecord).where(
            AbilityBindingRecord.system == system,
            AbilityBindingRecord.binding_id == binding_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_effect(self, session: AsyncSession, system: str, effect_id: str) -> EffectDefinitionRecord | None:
        stmt = select(EffectDefinitionRecord).where(
            EffectDefinitionRecord.system == system,
            EffectDefinitionRecord.effect_id == effect_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    def _version_is_newer(self, incoming: str, existing: str) -> bool:
        return self._version_key(incoming) > self._version_key(existing)

    def _version_key(self, value: str) -> tuple[int, ...]:
        if not value:
            return (0,)
        parts = re.findall(r"\d+", value)
        if not parts:
            return (0,)
        return tuple(int(part) for part in parts)
