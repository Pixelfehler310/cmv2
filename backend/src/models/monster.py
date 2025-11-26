from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base
from .mixins import UUIDMixin, TimestampMixin

class Monster(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "monsters"

    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    size: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    alignment: Mapped[str] = mapped_column(String)
    
    # Stats
    armor_class: Mapped[int] = mapped_column(Integer)
    hit_points: Mapped[int] = mapped_column(Integer)
    hit_dice: Mapped[str] = mapped_column(String)
    speed: Mapped[dict] = mapped_column(JSON) # {"walk": 30, "fly": 60}
    
    # Ability Scores
    strength: Mapped[int] = mapped_column(Integer)
    dexterity: Mapped[int] = mapped_column(Integer)
    constitution: Mapped[int] = mapped_column(Integer)
    intelligence: Mapped[int] = mapped_column(Integer)
    wisdom: Mapped[int] = mapped_column(Integer)
    charisma: Mapped[int] = mapped_column(Integer)
    
    # Complex Data
    proficiencies: Mapped[list] = mapped_column(JSON, default=list)
    senses: Mapped[dict] = mapped_column(JSON, default=dict)
    languages: Mapped[str] = mapped_column(String)
    challenge_rating: Mapped[float] = mapped_column(Integer) # Can be fraction? 1/4. Store as float 0.25
    xp: Mapped[int] = mapped_column(Integer)
    
    # Actions & Traits
    special_abilities: Mapped[list] = mapped_column(JSON, default=list)
    actions: Mapped[list] = mapped_column(JSON, default=list)
    legendary_actions: Mapped[list] = mapped_column(JSON, default=list)
    effects: Mapped[list] = mapped_column(JSON, default=list)
