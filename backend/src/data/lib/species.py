from sqlalchemy import String, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.common.database import Base
from src.common.mixins import UUIDMixin, TimestampMixin

class Species(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "species"

    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String)
    
    # Stats
    speed: Mapped[int] = mapped_column(Integer, default=30)
    size: Mapped[str] = mapped_column(String, default="Medium")
    
    # Data
    ability_bonuses: Mapped[dict] = mapped_column(JSON, default=dict) # {"dexterity": 2}
    traits: Mapped[list] = mapped_column(JSON, default=list) # List of Feature IDs or embedded data
    languages: Mapped[list] = mapped_column(JSON, default=list)
    effects: Mapped[list] = mapped_column(JSON, default=list)
