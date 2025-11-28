from sqlalchemy import String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base
from src.common.mixins import UUIDMixin, TimestampMixin
from uuid import UUID


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    social_auths: Mapped[list["UserSocialAuth"]] = relationship("UserSocialAuth", back_populates="user")


class UserSocialAuth(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_social_auths"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    provider: Mapped[str] = mapped_column(String)  # 'google', 'discord'
    provider_user_id: Mapped[str] = mapped_column(String)  # Unique ID from provider
    email: Mapped[str] = mapped_column(String, nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSON, default={})

    user: Mapped["User"] = relationship("User", back_populates="social_auths")
