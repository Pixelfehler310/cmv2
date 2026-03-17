from __future__ import annotations

from sqlalchemy import JSON, Boolean, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.common.mixins import TimestampMixin, UUIDMixin
from src.database import Base


class ActionDefinitionRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dnd5e_action_definitions"

    system: Mapped[str] = mapped_column(String, default="dnd5e", index=True)
    action_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    family: Mapped[str] = mapped_column(String, default="utility")
    action_type_cost: Mapped[str] = mapped_column(String, default="action")
    targeting_mode: Mapped[str] = mapped_column(
        String, default="single_target")
    range: Mapped[int | None] = mapped_column(Integer, nullable=True)
    save_context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    attack_context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    resource_costs: Mapped[list[dict]] = mapped_column(JSON, default=list)
    effect_intents: Mapped[list[dict]] = mapped_column(JSON, default=list)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_ref: Mapped[str] = mapped_column(String, default="custom")
    content_version: Mapped[str] = mapped_column(String, default="1")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    pack_id: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True)
    pack_version: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("system", "action_id",
                         name="uq_dnd5e_action_definition_system_action"),
    )


class AbilityBindingRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dnd5e_ability_bindings"

    system: Mapped[str] = mapped_column(String, default="dnd5e", index=True)
    binding_id: Mapped[str] = mapped_column(String, nullable=False)
    action_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    actor_template_id: Mapped[str | None] = mapped_column(
        String, nullable=True)
    actor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    unlock_conditions: Mapped[list[dict]] = mapped_column(JSON, default=list)
    override_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    pack_id: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True)
    pack_version: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("system", "binding_id",
                         name="uq_dnd5e_ability_binding_system_binding"),
    )


class EffectDefinitionRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dnd5e_effect_definitions"

    system: Mapped[str] = mapped_column(String, default="dnd5e", index=True)
    effect_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    family: Mapped[str] = mapped_column(String, default="utility")
    duration: Mapped[dict] = mapped_column(JSON, default=dict)
    stacking: Mapped[dict] = mapped_column(JSON, default=dict)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    modifiers: Mapped[list[dict]] = mapped_column(JSON, default=list)
    grants_conditions: Mapped[list[str]] = mapped_column(JSON, default=list)
    periodic: Mapped[list[dict]] = mapped_column(JSON, default=list)
    removal_triggers: Mapped[list[dict]] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    content_version: Mapped[str] = mapped_column(String, default="1")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    pack_id: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True)
    pack_version: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("system", "effect_id",
                         name="uq_dnd5e_effect_definition_system_effect"),
    )


class EffectInstanceRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dnd5e_effect_instances"

    instance_id: Mapped[str] = mapped_column(
        String, nullable=False, unique=True, index=True)
    effect_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    source_actor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    target_actor_id: Mapped[str] = mapped_column(
        String, nullable=False, index=True)
    applied_at_round: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining_duration: Mapped[int | None] = mapped_column(
        Integer, nullable=True)
    concentration_owner_actor_id: Mapped[str | None] = mapped_column(
        String, nullable=True)
    stack_count: Mapped[int] = mapped_column(Integer, default=1)
    snapshot_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict)
    encounter_session_id: Mapped[str | None] = mapped_column(
        ForeignKey("dnd5e_encounter_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )


Index("ix_dnd5e_action_definitions_system_pack",
      ActionDefinitionRecord.system, ActionDefinitionRecord.pack_id)
Index("ix_dnd5e_ability_bindings_system_pack",
      AbilityBindingRecord.system, AbilityBindingRecord.pack_id)
Index("ix_dnd5e_effect_definitions_system_pack",
      EffectDefinitionRecord.system, EffectDefinitionRecord.pack_id)
