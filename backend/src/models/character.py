from sqlalchemy import String, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base
from .mixins import UUIDMixin, TimestampMixin
from .species import Species
from .class_model import ClassModel
from .background import Background

class Character(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "characters"

    name: Mapped[str] = mapped_column(String, index=True)
    player_name: Mapped[str] = mapped_column(String, nullable=True)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), nullable=True)
    
    # Core Identity
    species_id: Mapped[str] = mapped_column(ForeignKey("species.id"), nullable=True)
    class_id: Mapped[str] = mapped_column(ForeignKey("classes.id"), nullable=True)
    background_id: Mapped[str] = mapped_column(ForeignKey("backgrounds.id"), nullable=True)
    
    level: Mapped[int] = mapped_column(Integer, default=1)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    alignment: Mapped[str] = mapped_column(String, nullable=True)
    
    # Relationships
    species: Mapped["Species"] = relationship()
    char_class: Mapped["ClassModel"] = relationship()
    background: Mapped["Background"] = relationship()
    
    # Stats (Base values, modifiers calculated in logic)
    strength: Mapped[int] = mapped_column(Integer, default=10)
    dexterity: Mapped[int] = mapped_column(Integer, default=10)
    constitution: Mapped[int] = mapped_column(Integer, default=10)
    intelligence: Mapped[int] = mapped_column(Integer, default=10)
    wisdom: Mapped[int] = mapped_column(Integer, default=10)
    charisma: Mapped[int] = mapped_column(Integer, default=10)
    
    # Vitals
    max_hp: Mapped[int] = mapped_column(Integer)
    current_hp: Mapped[int] = mapped_column(Integer)
    temp_hp: Mapped[int] = mapped_column(Integer, default=0)
    hit_dice: Mapped[str] = mapped_column(String) # e.g. "1d8"
    armor_class: Mapped[int] = mapped_column(Integer, default=10)
    speed: Mapped[int] = mapped_column(Integer, default=30)
    initiative: Mapped[int] = mapped_column(Integer, default=0)
    
    # State & Inventory
    inventory: Mapped[list] = mapped_column(JSON, default=list) # List of Item instances (with equipped status)
    spells: Mapped[list] = mapped_column(JSON, default=list) # List of Known Spells
    spell_slots: Mapped[dict] = mapped_column(JSON, default=dict) # {"1": 2, "2": 0}
    actions: Mapped[list] = mapped_column(JSON, default=list) # Custom/Explicit Actions
    effects: Mapped[list] = mapped_column(JSON, default=list) # Active effects
    
    # Relationships
    campaign: Mapped["Campaign"] = relationship(back_populates="characters")
