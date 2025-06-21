from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from fastapi.responses import JSONResponse
from models import User
from auth import hash_password, verify_password
from mfa import generate_mfa_secret, verify_mfa_token, get_totp_uri
from schemas import UserCreate, UserLogin

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    

@app.post("/register")
def create_user(user: UserCreate , db: Session = Depends(get_db)):
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
    return JSONResponse(
        status_code=201,
        content={
            "message": "User created successfully", "mfa_uri": uri})

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    if not verify_mfa_token(db_user.mfa_secret, user.mfa_code):
        raise HTTPException(status_code=401, detail="Invalid MFA code")
    
    return JSONResponse(
        status_code=200,
        content={
            "message": "Login successful"
        }
    )