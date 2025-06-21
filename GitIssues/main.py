from fastapi import FastAPI, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from fastapi.responses import JSONResponse
from models import User
from auth import hash_password, verify_password, generate_mfa_secret, get_totp_uri, verify_mfa_token
from jwt_token import create_access_token, verify_token, get_current_user, oauth2_scheme
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from schemas import DeleteUser, UserCreate, UserLogin, ForgetPassword
from GitIssues.schemas import GithubIssue
import httpx
app = FastAPI()


GITHUB_TOKEN = "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"
GITHUB_REPO = "rckr2710/RetriFix-App"

@app.post("/github-issue")
async def create_github_issue(issue: GithubIssue):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    data = {
        "title": issue.title,
        "body": issue.body
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json=data)

    if response.status_code == 201:
        return {
            "message": "Issue created successfully",
            "url": response.json().get("html_url")
        }
    else:
        raise HTTPException(status_code=response.status_code, detail=response.json())