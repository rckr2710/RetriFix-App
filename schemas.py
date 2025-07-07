from datetime import datetime
from typing import List, Optional
from uuid import UUID  # Import UUID
from pydantic import BaseModel, validator


class LdapUser(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class ChatCreateRequest(BaseModel):
    title: str = "new chat"


class ChatResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime

    class Config:
        orm_mode = True


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    image_url: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True

class UserChatList(BaseModel):
    id: UUID
    title: str
    created_at: datetime

    class Config:
        orm_mode = True

class ChatMessages(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    messages: List[MessageResponse]

    class Config:
        orm_mode = True