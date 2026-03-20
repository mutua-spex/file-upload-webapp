from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 0


class TokenData(BaseModel):
    username: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        orm_mode = True


class RoomCreate(BaseModel):
    name: str
    description: Optional[str] = None


class RoomRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True


class MessageCreate(BaseModel):
    content: Optional[str] = None
    attachment_url: Optional[str] = None


class MessageRead(BaseModel):
    id: int
    room_id: int
    sender_id: int
    content: Optional[str] = None
    attachment_url: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True


class RefreshTokenRequest(BaseModel):
    refresh_token: str
