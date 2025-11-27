from sqlalchemy import String, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.common.database import Base
from src.common.mixins import UUIDMixin, TimestampMixin

class Background(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "backgrounds"

    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String)
    
    skill_proficiencies: Mapped[list] = mapped_column(JSON, default=list)
    tool_proficiencies: Mapped[list] = mapped_column(JSON, default=list)
    equipment: Mapped[list] = mapped_column(JSON, default=list)
    feature: Mapped[dict] = mapped_column(JSON, default=dict) # The main background feature
    effects: Mapped[list] = mapped_column(JSON, default=list)
