from fastapi import FastAPI, Depends, HTTPException, Header, Security
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from fastapi.responses import JSONResponse
from models import User
from auth import hash_password, verify_password, generate_mfa_secret, get_totp_uri, verify_mfa_token
from jwt_token import create_access_token, verify_token, get_current_user
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from schemas import DeleteUser, UserCreate, UserLogin, ForgetPassword
from fastapi import Header
from fastapi import Cookie

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
    

# @app.post("/register")
# def register(user: UserCreate , db: Session = Depends(get_db)):
#     existing_user = db.query(User).filter(User.username == user.username).first()
#     if existing_user:
#         raise HTTPException(status_code=400, detail="Username already exists")
#     db_user = User(
#         username=user.username,
#         password=hash_password(user.password),
#         mfa_secret=generate_mfa_secret(),
#     )
#     uri = get_totp_uri(user.username, secret=db_user.mfa_secret)
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return JSONResponse(content={"uri": uri})


@app.post("/login")
def login(request_model: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == request_model.username).first()
    if not db_user:
        # New user: register and send MFA QR
        mfa_secret = generate_mfa_secret()
        db_user = User(
            username=request_model.username,
            mfa_secret=mfa_secret
        )
        uri = get_totp_uri(request_model.username, secret=mfa_secret)

        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        # Set cookies for username
        response = JSONResponse(content={"message": "New user registered", "MFAuri": uri})
        response.set_cookie(
            key="username",
            value=request_model.username,
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
        value=request_model.username,
        httponly=True,
        max_age=1800,
        secure=False,
        samesite="Lax",
    )
    return response

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





@app.put("/forget-password")
def forget_password(request_model: ForgetPassword ,db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == request_model.username).first()
    # if not db_user:
    #     raise HTTPException(status_code=404, detail="User not found")
    if request_model.password != request_model.repeat_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if not request_model.password or not request_model.repeat_password:
        raise HTTPException(status_code=400, detail="Password cannot be empty")
    db_user.password = hash_password(request_model.password)
    db.commit()
    db.refresh(db_user)
    return {"message": "Password updated successfully"}

@app.get("/verify-user")
def verify_user(username: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    # user need to stored in local storage
    # fetch user details from the local storage
    return {"message": "User exists"}
    
   
@app.post("/logout")
def logout():
    response = JSONResponse(content={"message": "Logged out, cookies cleared"})
    # Clear all known cookies
    response.delete_cookie(key="username")
    response.delete_cookie(key="access_token")
    
    return response