import os
from typing import List, Optional
from uuid import uuid4
from fastapi import FastAPI, Depends, Form, HTTPException, Header, Security, requests
import httpx
from pydantic import BaseModel
from sqlalchemy.orm import Session
from GitIssues.schemas import GitLabIssue
from database import SessionLocal, engine, Base, get_db
from fastapi.responses import JSONResponse
from models import ChatSession, Message, User
from auth import hash_password, verify_password, generate_mfa_secret, get_totp_uri, verify_mfa_token
from jwt_token import create_access_token, verify_token, get_current_user
from fastapi import Cookie
from ldap3 import Server, Connection, ALL
from ldap3.core.exceptions import LDAPException
from ldap3.utils.hashed import hashed
from passlib.hash import ldap_salted_sha1
from fastapi import File, UploadFile
from schemas import ChatCreateRequest, ChatResponse, MessageCreateRequest, MessagePairResponse, MessageResponse, UserLogin, LdapUser
from config import settings

app = FastAPI()

# Base.metadata.create_all(bind=engine)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

# To list users in ldap
# ldapsearch -x -H ldap://localhost -D "cn=admin,dc=local" -w admin -b "dc=local"


@app.post("/add-users")
def add_users(users: List[LdapUser]):
    try:
        server = Server(settings.LDAP_SERVER, get_info=ALL)
        conn = Connection(server, user=settings.ADMIN_DN, password=settings.ADMIN_PASSWORD, auto_bind=True)
        added = []
        for user in users:
            user_dn = f"uid={user.username},{settings.BASE_DN}"

            # Check if user already exists
            if conn.search(settings.BASE_DN, f"(uid={user.username})", attributes=["uid"]):
                continue  # skip existing
            attributes = {
                "objectClass": ["inetOrgPerson"],
                "uid": user.username,
                "cn": user.username,
                "sn": user.username,
                "userPassword": ldap_salted_sha1.hash(user.password)
            }
            conn.add(dn=user_dn, attributes=attributes)
            if conn.result["description"] == "success":
                added.append(user.username)
            else:
                raise HTTPException(status_code=500, detail=f"Failed to add {user.username}")
        return {"message": "Users added successfully", "added": added}
    except LDAPException as e:
        raise HTTPException(status_code=500, detail=f"LDAP error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/login")
def ldap_login(user: UserLogin,db: Session = Depends(get_db)):
    user_dn = f"uid={user.username},{settings.BASE_DN}"
    try:
        server = Server(settings.LDAP_SERVER, get_info=ALL)
        conn = Connection(server, user=user_dn, password=user.password)
        if not conn.bind():
            raise HTTPException(status_code=401, detail="Invalid username or password")
        # {"message": f"User {request.username} authenticated successfully"}
        db_user = db.query(User).filter(User.username == user.username).first()
        if not db_user:
            # New user: register and send MFA QR
            mfa_secret = generate_mfa_secret()
            db_user = User(
                username=user.username,
                mfa_secret=mfa_secret
            )
            uri = get_totp_uri(user.username, secret=mfa_secret)

            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            # Set cookies for username
            response = JSONResponse(content={"message": "New user registered", "MFAuri": uri})
            response.set_cookie(
                key="username",
                value=user.username,
                httponly=True,
                max_age=1800,
                secure=False,
                samesite="Lax",
            )
            return response
        # Existing user: proceed to MFA verification step
        access_token= create_access_token(data={"sub": user.username})
        response = JSONResponse(content={"message": "Existing user, proceed to MFA verification"})
        response.set_cookie(
            key="username",
            value=user.username,
            httponly=True,
            max_age=1800,
            secure=False,
            samesite="Lax",
        )
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=1800,
            secure=False,
            samesite="Lax",
        )
        return response

    except LDAPException:
        raise HTTPException(status_code=401, detail="LDAP authentication failed")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    

@app.get("/verify-mfa")
def verify_mfa(mfa_code: str,username: str = Cookie(None),db: Session = Depends(get_db)):
    if not username:
        raise HTTPException(status_code=400, detail="Username not found in cookie")
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_mfa_token(db_user.mfa_secret, mfa_code):
        raise HTTPException(status_code=401, detail="Invalid MFA code")
    access_token = create_access_token(data={"sub": username})
    response = JSONResponse(content={"message": "MFA verification successful"})

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=1800,
        secure=False,
        samesite="Lax"
    )
    return response

# Create chat session for user
@app.post("/chats", response_model=ChatResponse)
def create_chat(req: ChatCreateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    new_chat = ChatSession(user_id=user.id, title=req.title)
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat

# Get all chat sessions for user
@app.get("/chats")
def list_chats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chats = db.query(ChatSession).filter_by(user_id=user.id, is_deleted=False).order_by(ChatSession.updated_at.desc()).all()
    if not chats:
        raise HTTPException(status_code=404, detail="No chats found")
    messages = db.query(Message).filter(Message.chat_id.in_([chat.id for chat in chats])).all()
    return [{
        "id": chat.id,
        "title": chat.title,
        "created_at": chat.created_at,
        "messages": [msg for msg in messages if msg.chat_id == chat.id]
    } for chat in chats]

# Delete a chat session
@app.delete("/chats/{chat_id}")
def delete_chat(chat_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = db.query(ChatSession).filter_by(id=chat_id, user_id=user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    chat.is_deleted = True
    db.commit()
    return {"message": "Chat deleted"}

# Get messages for a specific chat
@app.get("/chats/{chat_id}/messages", response_model=List[MessageResponse])
def get_chat_messages(chat_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = db.query(ChatSession).filter_by(id=chat_id, user_id=user.id, is_deleted=False).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat.messages



def generate_ai_response(messages: List[Message]) -> str:
    """
    Dummy model response generator for testing.
    Returns a mock reply based on the last user message.
    """
    last_user_message = next((m for m in reversed(messages) if m.role == "user"), None)
    if last_user_message:
        return f"Mock reply to: '{last_user_message.content}'"
    return "Hello! This is a test response."



# UPLOAD_DIR = "uploaded_images"
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

@app.post("/chats/{chat_id}/messages")
async def create_message(
    chat_id: str,
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


@app.delete("/logout")
def logout(user: User = Depends(get_current_user)):
    response = JSONResponse(content={"message": f"User '{user.username}' logged out, cookies cleared."})
    # Clear all known cookies
    response.delete_cookie(key="username")
    response.delete_cookie(key="access_token")
    
    return response
