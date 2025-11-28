from sqlalchemy import String, Integer, JSON, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base
from src.common.mixins import UUIDMixin, TimestampMixin


class Feature(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "features"

    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String)
    # e.g. "Class: Fighter", "Race: Elf"
    source: Mapped[str] = mapped_column(String)
    level_required: Mapped[int] = mapped_column(Integer, default=1)

    # Effects provided by this feature
    effects: Mapped[list] = mapped_column(JSON, default=list)
