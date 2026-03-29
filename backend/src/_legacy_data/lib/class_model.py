from sqlalchemy import String, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base
from src.common.mixins import UUIDMixin, TimestampMixin


class ClassModel(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "classes"

    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String)
    hit_die: Mapped[str] = mapped_column(String)  # "1d8"

    # Data
    proficiencies: Mapped[dict] = mapped_column(
        JSON, default=dict)  # {"armor": [], "weapons": []}
    saving_throws: Mapped[list] = mapped_column(
        JSON, default=list)  # ["strength", "constitution"]

    # Progression table could be complex, storing as JSON for now
    progression: Mapped[list] = mapped_column(JSON, default=list)
    effects: Mapped[list] = mapped_column(JSON, default=list)
    # features: Mapped[list] = mapped_column(JSON, default=list) # Linked features by level
