from sqlalchemy import String, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base
from .mixins import UUIDMixin, TimestampMixin

class Feat(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "feats"

    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String)
    prerequisites: Mapped[str] = mapped_column(String, nullable=True)
    
    effects: Mapped[list] = mapped_column(JSON, default=list)
