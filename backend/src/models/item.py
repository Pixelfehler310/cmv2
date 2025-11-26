from sqlalchemy import String, Integer, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base
from .mixins import UUIDMixin, TimestampMixin

class Item(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "items"

    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String) # Weapon, Armor, Potion, etc.
    rarity: Mapped[str] = mapped_column(String)
    weight: Mapped[float] = mapped_column(Integer, default=0) # Stored as float in logic, but let's use Integer for now or Float? Python float is fine. SQLAlchemy Float.
    price: Mapped[int] = mapped_column(Integer, default=0) # In copper pieces
    
    # JSONB for dynamic properties
    properties: Mapped[dict] = mapped_column(JSON, default=dict)
    effects: Mapped[list] = mapped_column(JSON, default=list)
