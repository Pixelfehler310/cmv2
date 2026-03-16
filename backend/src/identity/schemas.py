from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    username: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
