from datetime import datetime, timedelta
from urllib import request
from jose import JWTError, jwt
from fastapi import Cookie, FastAPI, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from database import get_db
from models import User

SECRET_KEY = "RetriFix-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
    
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


# def get_current_user(access_token: str = Cookie(None)):
#     if not access_token:
#         raise HTTPException(status_code=401, detail="Missing token in cookie")
#     payload = verify_token(access_token)
#     if not payload:
#         raise HTTPException(status_code=401, detail="Invalid or expired token")
#     return payload["sub"]

def get_current_user(access_token: str = Cookie(None),db: Session = Depends(get_db)) -> User:
    if not access_token:
        raise HTTPException(status_code=401, detail="Missing token")
    
    payload = verify_token(access_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    user = db.query(User).filter_by(username=username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user