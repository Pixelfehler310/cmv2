from __future__ import annotations

from sqlalchemy import JSON, Boolean, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.mixins import TimestampMixin, UUIDMixin
from src.database import Base


class EncounterSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dnd5e_encounter_sessions"

    campaign_id: Mapped[str] = mapped_column(String, index=True, unique=True)
    encounter_id: Mapped[str] = mapped_column(String, nullable=False)
    phase: Mapped[str] = mapped_column(String, default="pre_combat")
    round_number: Mapped[int] = mapped_column(Integer, default=0)
    active_index: Mapped[int] = mapped_column(Integer, default=0)
    combat_state_json: Mapped[dict] = mapped_column(JSON, default=dict)

    combatants: Mapped[list["CombatantState"]] = relationship(
        back_populates="encounter_session",
        cascade="all, delete-orphan",
    )
    turn_budgets: Mapped[list["TurnBudgetRecord"]] = relationship(
        back_populates="encounter_session",
        cascade="all, delete-orphan",
    )
    action_logs: Mapped[list["ActionLog"]] = relationship(
        back_populates="encounter_session",
        cascade="all, delete-orphan",
    )


class CombatantState(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dnd5e_combatant_states"

    encounter_session_id: Mapped[str] = mapped_column(
        ForeignKey("dnd5e_encounter_sessions.id", ondelete="CASCADE"),
        index=True,
    )
    actor_id: Mapped[str] = mapped_column(String, index=True)
    initiative_order: Mapped[int] = mapped_column(Integer, default=0)
    owner_user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    current_hp: Mapped[int] = mapped_column(Integer, default=0)
    max_hp: Mapped[int] = mapped_column(Integer, default=0)
    pos_x: Mapped[int] = mapped_column(Integer, default=0)
    pos_y: Mapped[int] = mapped_column(Integer, default=0)
    actor_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)

    encounter_session: Mapped[EncounterSession] = relationship(
        back_populates="combatants")
    turn_budgets: Mapped[list["TurnBudgetRecord"]] = relationship(
        back_populates="combatant",
        cascade="all, delete-orphan",
    )


class TurnBudgetRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dnd5e_turn_budget_records"

    encounter_session_id: Mapped[str] = mapped_column(
        ForeignKey("dnd5e_encounter_sessions.id", ondelete="CASCADE"),
        index=True,
    )
    combatant_id: Mapped[str] = mapped_column(
        ForeignKey("dnd5e_combatant_states.id", ondelete="CASCADE"),
        index=True,
    )
    round_number: Mapped[int] = mapped_column(Integer, default=1)
    action_available: Mapped[bool] = mapped_column(Boolean, default=True)
    bonus_action_available: Mapped[bool] = mapped_column(Boolean, default=True)
    reaction_available: Mapped[bool] = mapped_column(Boolean, default=True)
    max_movement: Mapped[int] = mapped_column(Integer, default=30)
    movement_used: Mapped[int] = mapped_column(Integer, default=0)

    encounter_session: Mapped[EncounterSession] = relationship(
        back_populates="turn_budgets")
    combatant: Mapped[CombatantState] = relationship(
        back_populates="turn_budgets")

    __table_args__ = (
        UniqueConstraint(
            "encounter_session_id",
            "combatant_id",
            "round_number",
            name="uq_dnd5e_budget_encounter_combatant_round",
        ),
    )


class ActionLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dnd5e_action_logs"

    encounter_session_id: Mapped[str] = mapped_column(
        ForeignKey("dnd5e_encounter_sessions.id", ondelete="CASCADE"),
        index=True,
    )
    request_id: Mapped[str | None] = mapped_column(String, nullable=True)
    actor_id: Mapped[str] = mapped_column(String, index=True)
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    action_state: Mapped[str] = mapped_column(String, nullable=False)
    denial_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    authorization_checks: Mapped[dict] = mapped_column(JSON, default=dict)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)

    encounter_session: Mapped[EncounterSession] = relationship(
        back_populates="action_logs")


Index("ix_dnd5e_budget_encounter_round",
      TurnBudgetRecord.encounter_session_id, TurnBudgetRecord.round_number)
Index("ix_dnd5e_budget_encounter_combatant",
      TurnBudgetRecord.encounter_session_id, TurnBudgetRecord.combatant_id)
