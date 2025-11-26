from sqlalchemy import String, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base
from .mixins import UUIDMixin, TimestampMixin

class Campaign(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "campaigns"

    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    dm_id: Mapped[str] = mapped_column(String, nullable=True) # User ID of the DM
    
    # State
    current_scene: Mapped[str] = mapped_column(String, nullable=True)
    active_turn: Mapped[str] = mapped_column(String, nullable=True) # Character ID whose turn it is
    
    # Relationships
    characters: Mapped[list["Character"]] = relationship(back_populates="campaign", cascade="all, delete-orphan")
