from typing import List, Optional
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
# from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
# from schemas import DeleteUser, UserCreate, UserLogin, ForgetPassword
# from fastapi import Header
from fastapi import Cookie
from ldap3 import Server, Connection, ALL
from ldap3.core.exceptions import LDAPException, LDAPBindError
from ldap3.utils.hashed import hashed
from passlib.hash import ldap_salted_sha1
from fastapi import File, UploadFile
from schemas import ChatCreateRequest, ChatResponse, MessageCreateRequest, MessageResponse, UserLogin

app = FastAPI()

# Base.metadata.create_all(bind=engine)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


LDAP_SERVER = "ldap://localhost:389"
ADMIN_DN = "cn=admin,dc=local"
ADMIN_PASSWORD = "admin"
BASE_DN = "dc=local"



@app.post("/login")
def ldap_login(user: UserLogin,db: Session = Depends(get_db)):
    user_dn = f"uid={user.username},{BASE_DN}"
    try:
        server = Server(LDAP_SERVER, get_info=ALL)
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


@app.post("/chats", response_model=ChatResponse)
def create_chat(req: ChatCreateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    new_chat = ChatSession(user_id=user.id, title=req.title)
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat

# Get all chat sessions for user
@app.get("/chats", response_model=List[ChatResponse])
def list_chats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chats = db.query(ChatSession).filter_by(user_id=user.id, is_deleted=False).order_by(ChatSession.updated_at.desc()).all()
    return chats

# Delete a chat session (soft delete)
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



def generate_assistant_response(messages: List[Message]) -> str:
    """
    Dummy model response generator for testing.
    Returns a mock reply based on the last user message.
    """
    last_user_message = next((m for m in reversed(messages) if m.role == "user"), None)
    if last_user_message:
        return f"Mock reply to: '{last_user_message.content}'"
    return "Hello! This is a test response."


@app.post("/chats/{chat_id}/messages", response_model=MessageResponse)
def create_message_with_response(chat_id: int,req: MessageCreateRequest,db: Session = Depends(get_db),user: User = Depends(get_current_user)):
    chat = db.query(ChatSession).filter(
        ChatSession.id == chat_id,
        ChatSession.user_id == user.id,
        ChatSession.is_deleted == False
    ).first()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found or access denied")
    user_msg = Message(chat_id=chat_id,role="user",content=req.content)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    db.refresh(chat)
    assistant_reply = generate_assistant_response(chat.messages)
    # Store ai message
    assistant_msg = Message(chat_id=chat_id,role="ai",content=assistant_reply)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return assistant_msg

@app.delete("/logout")
def logout(user: User = Depends(get_current_user)):
    response = JSONResponse(content={"message": f"User '{user.username}' logged out, cookies cleared."})
    # Clear all known cookies
    response.delete_cookie(key="username")
    response.delete_cookie(key="access_token")
    
    return response
