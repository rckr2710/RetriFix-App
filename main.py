from typing import List
from fastapi import FastAPI, Depends, HTTPException, Header, Security
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from fastapi.responses import JSONResponse
from models import User
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

from schemas import UserLogin

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
        response = JSONResponse(content={"message": "Existing user, proceed to MFA verification"})
        response.set_cookie(
            key="username",
            value=user.username,
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
    
    


# class SimpleUser(BaseModel):
#     username: str
#     password: str

# @app.post("/users")
# def add_simple_users(users: List[SimpleUser]):
#     try:
#         server = Server(LDAP_SERVER, get_info=ALL)
#         conn = Connection(server, user=ADMIN_DN, password=ADMIN_PASSWORD, auto_bind=True)

#         added = []
#         for user in users:
#             user_dn = f"uid={user.username},{BASE_DN}"

#             # Optional: skip if already exists
#             if conn.search(BASE_DN, f"(uid={user.username})", attributes=["uid"]):
#                 continue

#             hashed_password = ldap_salted_sha1.hash(user.password)

#             attributes = {
#                 "objectClass": ["inetOrgPerson"],
#                 "uid": user.username,
#                 "cn": user.username,
#                 "sn": user.username,
#                 "userPassword": hashed_password,
#             }

#             conn.add(user_dn, attributes=attributes)

#             if conn.result["description"] == "success":
#                 added.append(user.username)
#             else:
#                 raise HTTPException(status_code=500, detail=f"Failed to add {user.username}: {conn.result}")

#         return {"message": "Users added successfully", "added": added}

#     except LDAPException as e:
#         raise HTTPException(status_code=500, detail=f"LDAP error: {str(e)}")

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")





# @app.post("/login")
# def login(request_model: UserLogin, db: Session = Depends(get_db)):
#     db_user = db.query(User).filter(User.username == request_model.username).first()
#     if not db_user:
#         # New user: register and send MFA QR
#         mfa_secret = generate_mfa_secret()
#         db_user = User(
#             username=request_model.username,
#             mfa_secret=mfa_secret
#         )
#         uri = get_totp_uri(request_model.username, secret=mfa_secret)

#         db.add(db_user)
#         db.commit()
#         db.refresh(db_user)
#         # Set cookies for username
#         response = JSONResponse(content={"message": "New user registered", "MFAuri": uri})
#         response.set_cookie(
#             key="username",
#             value=request_model.username,
#             httponly=True,
#             max_age=1800,
#             secure=False,
#             samesite="Lax",
#         )
#         return response
#     # Existing user: proceed to MFA verification step
#     response = JSONResponse(content={"message": "Existing user, proceed to MFA verification"})
#     response.set_cookie(
#         key="username",
#         value=request_model.username,
#         httponly=True,
#         max_age=1800,
#         secure=False,
#         samesite="Lax",
#     )
#     return response

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

@app.post("/logout")
def logout(get_current_user: str = Depends(get_current_user)):
    response = JSONResponse(content={"message": "Logged out, cookies cleared"})
    # Clear all known cookies
    response.delete_cookie(key="username")
    response.delete_cookie(key="access_token")
    
    return response