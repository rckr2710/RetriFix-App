from fastapi import FastAPI, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from fastapi.responses import JSONResponse
from models import User
from auth import hash_password, verify_password, generate_mfa_secret, get_totp_uri, verify_mfa_token
from jwt_token import create_access_token, verify_token, get_current_user, oauth2_scheme
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from schemas import DeleteUser, UserCreate, UserLogin, ForgetPassword

app = FastAPI()


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
    return uri

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid password")
    if not verify_mfa_token(db_user.mfa_secret, user.mfa_code):
        raise HTTPException(status_code=401, detail="Invalid MFA code")
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token}


@app.put("/forget-password")
def forget_password(request_model: ForgetPassword ,db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == request_model.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.password = hash_password(request_model.new_password)
    db.commit()
    db.refresh(db_user)
    return {"message": "Password updated successfully"}

@app.get("/user/{username}")
def get_user(username: str, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"User Found"}


@app.delete("/reset")
def delete_user(request_model: DeleteUser,db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_user=db.query(User).filter(User.username == request_model.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)      
    db.commit()
    return {"message": f"{request_model.username} User deleted successfully"}








# from GitIssues.schemas import GithubIssue
# import httpx
# app = FastAPI()

# GITHUB_TOKEN = "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"
# GITHUB_REPO = "rckr2710/RetriFix-App"

# @app.post("/github-issue")
# async def create_github_issue(issue: GithubIssue):
#     url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    
#     headers = {
#         "Authorization": f"token {GITHUB_TOKEN}",
#         "Accept": "application/vnd.github+json"
#     }

#     data = {
#         "title": issue.title,
#         "body": issue.body
#     }

#     async with httpx.AsyncClient(timeout=30.0) as client:
#         response = await client.post(url, headers=headers, json=data)

#     if response.status_code == 201:
#         return {
#             "message": "Issue created successfully",
#             "url": response.json().get("html_url")
#         }
#     else:
#         raise HTTPException(status_code=response.status_code, detail=response.json())