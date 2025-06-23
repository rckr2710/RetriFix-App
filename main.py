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
    

@app.post("/register")
def register(user: UserCreate , db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    db_user = User(
        username=user.username,
        password=hash_password(user.password),
        mfa_secret=generate_mfa_secret(),
    )
    uri = get_totp_uri(user.username, secret=db_user.mfa_secret)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return JSONResponse(content={"uri": uri})

@app.post("/login")
def login(request_model: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == request_model.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(request_model.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_mfa_token(db_user.mfa_secret, request_model.mfa_code):
        raise HTTPException(status_code=401, detail="Invalid MFA code")
    
    access_token = create_access_token(data={"sub": db_user.username})
    return JSONResponse(content={"access_token": access_token})

# @app.get("/verify-mfa")
# def verify_mfa(mfa_code: str,username: str = Cookie(None),db: Session = Depends(get_db)):
#     db_user = db.query(User).filter(User.username == username).first()
#     if not db_user:
#         raise HTTPException(status_code=404, detail="User not found")
#     if not verify_mfa_token(db_user.mfa_secret, mfa_code):
#         raise HTTPException(status_code=401, detail="Invalid MFA code")
#     access_token = create_access_token(data={"sub": db_user.username})
#     response = JSONResponse(content={"access_token": access_token})
#     return response


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
    return {"message": "User exists"}

@app.get("/user")
def get_user(username: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    # user need to stored in local storage
    # fetch user details from the local storage
    return {"User Found"}


@app.delete("/reset")
def delete_user(request_model: DeleteUser,db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_user=db.query(User).filter(User.username == request_model.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)      
    db.commit()
    return {"message": f"{request_model.username} User deleted successfully"}
   