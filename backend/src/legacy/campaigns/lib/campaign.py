from sqlalchemy import String, Integer, JSON, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base
from src.common.mixins import UUIDMixin, TimestampMixin
import enum


class CampaignRole(str, enum.Enum):
    DM = "DM"
    PLAYER = "PLAYER"
    SPECTATOR = "SPECTATOR"


class CampaignMember(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "campaign_members"
    __table_args__ = (
        UniqueConstraint(
            "campaign_id",
            "user_id",
            name="uq_campaign_members_campaign_id_user_id",
        ),
    )

    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    role: Mapped[CampaignRole] = mapped_column(
        String, default=CampaignRole.PLAYER)

    # Optional: Link to a specific character if they are a player
    active_character_id: Mapped[str] = mapped_column(String, nullable=True)

    campaign: Mapped["Campaign"] = relationship(back_populates="members")
    # user relationship would be here if we need it, but avoiding circular imports with identity module


class Campaign(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "campaigns"

    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    # dm_id is now redundant but we can keep it for quick lookup or legacy support
    dm_id: Mapped[str] = mapped_column(String, nullable=True)

    # State
    current_scene: Mapped[str] = mapped_column(String, nullable=True)
    active_encounter_id: Mapped[str] = mapped_column(String, nullable=True)
    context_version: Mapped[int] = mapped_column(Integer, default=0)
    active_turn: Mapped[str] = mapped_column(
        String, nullable=True)  # Character ID whose turn it is

    # Relationships
    characters: Mapped[list["Character"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan")

    members: Mapped[list["CampaignMember"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan")
