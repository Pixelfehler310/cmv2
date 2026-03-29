from sqlalchemy import String, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base
from src.common.mixins import UUIDMixin, TimestampMixin


class Faction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "factions"

    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String)
    goals: Mapped[str] = mapped_column(String, nullable=True)
    beliefs: Mapped[str] = mapped_column(String, nullable=True)
