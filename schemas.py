from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class LdapUser(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class ChatCreateRequest(BaseModel):
    title: Optional[str] = "New Chat"

class ChatResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        orm_mode = True

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        orm_mode = True


class MessageCreateRequest(BaseModel):
    role: Optional[str] = "user"
    content: str