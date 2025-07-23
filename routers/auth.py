
from typing import List
from fastapi import APIRouter, FastAPI, HTTPException, Depends, Cookie
from fastapi.responses import JSONResponse
from ldap3 import Server, Connection, ALL
from ldap3.core.exceptions import LDAPException
from passlib.hash import ldap_salted_sha1
from sqlalchemy.orm import Session
from fastapi import Depends
from auth import generate_mfa_secret, get_totp_uri, verify_mfa_token
from schemas import LdapUser, UserLogin
from config import settings
from database import get_db
from jwt_token import create_access_token, get_current_user
from models import User
import os

# app = FastAPI()
router = APIRouter(prefix="", tags=["Auth"])

# To list users in ldap
# ldapsearch -x -H ldap://localhost -D "cn=admin,dc=local" -w admin -b "dc=local"
# LDAP_SERVER=os.getenv("LDAP_SERVER","ldap://localhost:389")

@router.post("/add-users")
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


@router.post("/login")
def login(user: UserLogin,db: Session = Depends(get_db)):
    user_dn = f"uid={user.username},ou=users,{settings.BASE_DN}"
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
                httponly=False,
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
            httponly=False,
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
    

@router.get("/verify-mfa")
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


@router.delete("/logout")
def logout(user: User = Depends(get_current_user)):
    response = JSONResponse(content={"message": f"User '{user.username}' logged out, cookies cleared."})
    # Clear all known cookies
    response.delete_cookie(key="username")
    response.delete_cookie(key="access_token")
    
    return response

@router.get("/registered-users")
def get_registered_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    if not users:
        raise HTTPException(status_code=404, detail="No registered users found")
    count= len(users)
    return count
