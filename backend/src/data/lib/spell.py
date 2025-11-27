from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from src.common.database import Base
from src.common.mixins import UUIDMixin, TimestampMixin

class Spell(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "spells"

    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String)
    level: Mapped[int] = mapped_column(Integer)
    school: Mapped[str] = mapped_column(String)
    casting_time: Mapped[str] = mapped_column(String)
    range: Mapped[str] = mapped_column(String)
    components: Mapped[dict] = mapped_column(JSON) # V, S, M (with materials)
    duration: Mapped[str] = mapped_column(String)
    
    effects: Mapped[list] = mapped_column(JSON, default=list)
