
import os
import subprocess
import time
from typing import List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
import httpx
from sqlmodel import Session
from config import Settings
from database import get_db
from jwt_token import get_current_user
from models import ChatSession, Message, User
from schemas import ChatCreateRequest, ChatMessages, ChatResponse, MessageResponse, UserChatList
import logging
logging.basicConfig(level=logging.INFO)
# app = FastAPI()

router = APIRouter(prefix="", tags=["Chat"])

settings = Settings()

# UPLOAD_DIR = "uploaded_images"
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
# STREAM_SERVER_URL = os.getenv("STREAM_SERVER_URL", "http://localhost:8001/stream")


def generate_ai_response(messages: List[Message]) -> str:
    """
    Dummy model response generator for testing.
    Returns a large multi-paragraph mock reply.
    """
    last_user_message = next((m for m in reversed(messages) if m.role == "user"), None)
    if last_user_message:
        user_input = last_user_message.content
    else:
        user_input = "your message"

    return f"""Thank you for your message regarding "{user_input}".

We appreciate your interest and the points you've raised. To begin with, it's important to consider the foundational aspects of this topic. Many professionals overlook the basics, yet they are crucial to truly understanding the broader implications.

Secondly, when evaluating situations like these, it's beneficial to adopt a structured approach. One such method is to break the issue into smaller, more manageable components and analyze each in detail. This often uncovers hidden patterns or opportunities for improvement.

Moreover, communication and collaboration are key. Engaging with stakeholders and gathering diverse perspectives can greatly enhance the quality of your solution. Never underestimate the power of collective insight.

In conclusion, while this may seem like a complex matter at first glance, with the right mindset and methodology, it's entirely solvable. If you have any further questions or need additional clarification, feel free to ask — I'm here to help!

Best regards,
AI Assistant
"""


# @router.post("/chats/message/{chat_id}")
# async def create_message(
#     chat_id: UUID,
#     content: str = Form(...),
#     file: Optional[UploadFile] = File(None),
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user)
# ):
#     # 1. Validate Chat
#     chat = db.query(ChatSession).filter(
#         ChatSession.id == chat_id,
#         ChatSession.user_id == user.id,
#         ChatSession.is_deleted == False
#     ).first()
#     if not chat:
#         raise HTTPException(status_code=404, detail="Chat not found")

#     # 2. Handle image upload
#     image_url = None
#     if file:
#         ext = os.path.splitext(file.filename)[1]
#         filename = f"{uuid4().hex}{ext}"
#         path = os.path.join(settings.UPLOAD_DIR, filename)
#         with open(path, "wb") as f:
#             f.write(await file.read())
#         image_url = f"/images/{filename}"

#     # 3. Set chat title for first message
#     if db.query(Message).filter(Message.chat_id == chat_id).count() == 0:
#         first_five_words = " ".join(content.strip().split()[:5])
#         chat.title = first_five_words
#         db.add(chat)

#     # 4. Save user message
#     user_msg = Message(
#         chat_id=chat_id,
#         role="user",
#         content=content,
#         image_url=image_url
#     )
#     db.add(user_msg)
#     db.commit()
#     db.refresh(user_msg)

#     # 5. Call internal /stream endpoint to get AI reply
#     async with httpx.AsyncClient() as client:
#         try:
#             response = await client.post(
#                 STREAM_SERVER_URL,
#                 json={"query": content},
#                 timeout=60
#             )
#             print(f"AI stream response: {response.text}")
#             response.raise_for_status()
#             ai_reply = response.json()
#             if not ai_reply:
#                 raise ValueError("Empty AI response")
#             else:
#                 ai_msg = Message(
#                     chat_id=chat_id,
#                     role="assistant",
#                     content=ai_reply
#                 )
#                 db.add(ai_msg)
#                 db.commit()
#                 db.refresh(ai_msg)
#                 return ai_msg.content
#         except Exception as e:
#             print(f"Error from AI stream server: {str(e)}")
#             raise HTTPException(status_code=502, detail=f"Error from AI stream server: {str(e)}")
        
#     return {"message": "AI reply not generated due to an error."}

#     # 6. Save AI reply
#     # ai_msg = Message(
#     #     chat_id=chat_id,
#     #     role="assistant",
#     #     content=ai_reply
#     # )
#     # db.add(ai_msg)
#     # db.commit()
#     # db.refresh(ai_msg)

#     # 7. Return messages
#     # return {
#     #     "user_message": {
#     #         "content": user_msg.content,
#     #         "image_url": user_msg.image_url
#     #     },
#     #     "assistant_reply": {
#     #         "content": ai_msg.content
#     #     }
#     # }




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
        
    # Check if it's the first message in the chat
    existing_messages = db.query(Message).filter(Message.chat_id == chat_id).count()
    if existing_messages == 0:
        first_five_words = " ".join(content.strip().split()[:5])
        chat.title = first_five_words
        db.add(chat)

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
    # logging.info(f"AI server raw body: {ai_reply.text}")

    # Save AI message
    ai_msg = Message(
        chat_id=chat_id,
        role="assistant",
        content=ai_reply
    )
    logging.info(f"AI reply from JSON: {repr(ai_reply)}")
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






