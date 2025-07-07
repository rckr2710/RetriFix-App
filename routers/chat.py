
import os
from typing import List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, UploadFile
from sqlmodel import Session
from config import Settings
from database import get_db
from jwt_token import get_current_user
from models import ChatSession, Message, User
from schemas import ChatCreateRequest, ChatMessages, ChatResponse, MessageResponse, UserChatList

# app = FastAPI()

router = APIRouter(prefix="", tags=["Chat"])

settings = Settings()

# UPLOAD_DIR = "uploaded_images"
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

def generate_ai_response(messages: List[Message]) -> str:
    """
    Dummy model response generator for testing.
    Returns a mock reply based on the last user message.
    """
    last_user_message = next((m for m in reversed(messages) if m.role == "user"), None)
    if last_user_message:
        return f"Mock reply to: '{last_user_message.content}'"
    return "Hello! This is a test response."


@router.post("/chats/message/{chat_id}")
async def create_message(
    chat_id: UUID,
    content: str = Form(...),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    chat = db.query(ChatSession).filter(
        ChatSession.id == chat_id,
        ChatSession.user_id == user.id,
        ChatSession.is_deleted == False
    ).first()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Handle optional image
    image_url = None
    if file:
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid4().hex}{ext}"
        path = os.path.join(settings.UPLOAD_DIR, filename)
        with open(path, "wb") as f:
            f.write(await file.read())
        image_url = f"/images/{filename}"

    # Save user message
    user_msg = Message(
        chat_id=chat_id,
        role="user",
        content=content,
        image_url=image_url
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # Refresh messages (ensures new message included)
    db.refresh(chat)
    # Generate ai reply
    ai_reply = generate_ai_response(chat.messages)
    # Save AI message
    ai_msg = Message(
        chat_id=chat_id,
        role="assistant",
        content=ai_reply
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    return ai_msg.content

@router.post("/chats", response_model=ChatResponse)
def create_chat(req: Optional[ChatCreateRequest] = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    title = req.title if req and req.title else "new chat"
    chat = ChatSession(user_id=user.id, title=title)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat

# Put this chatids in react state
@router.get("/chats/chatlist", response_model=List[UserChatList])
def get_user_chats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")

    chats = (
        db.query(ChatSession)
        .filter_by(user_id=user.id, is_deleted=False)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return chats


# Get all chat sessions messages from user & ai
@router.get("/chats/{chat_id}", response_model=ChatMessages)
def get_chat_details(chat_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = db.query(ChatSession).filter_by(id=chat_id, user_id=user.id, is_deleted=False).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    # Refresh the chat to ensure messages are loaded
    db.refresh(chat)

    messages = db.query(Message)\
        .filter_by(chat_id=chat.id)\
        .order_by(Message.created_at.asc())\
        .all()

    chat.messages = messages

    return chat

# Delete a chat session
@router.delete("/chats/{chat_id}")
def delete_chat(chat_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = db.query(ChatSession).filter_by(id=chat_id, user_id=user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    chat.is_deleted = True
    db.commit()
    return {"message": "Chat deleted"}








