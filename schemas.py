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
    title: Optional[str] = "New Chat"
    
    @validator("title")
    def limit_to_five_words(cls, value):
        words = value.strip().split()
        if len(words) > 5:
            return " ".join(words[:5])  # truncate
        return value


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


# class MessageCreateRequest(BaseModel):
#     role: Optional[str] = "user"
#     content: str


# class MessagePairResponse(BaseModel):
#     messages: List[MessageResponse]

# class MessageResponse(BaseModel):
#     id: int  # or UUID if applicable
#     role: str  # 'user' or 'ai'
#     content: str
#     created_at: datetime

#     class Config:
#         orm_mode = True


class ChatMsgsResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    messages: List[MessageResponse]

    class Config:
        orm_mode = True