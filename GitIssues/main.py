from fastapi import FastAPI, Depends, HTTPException, Security, requests
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from fastapi.responses import JSONResponse
from models import User
from auth import hash_password, verify_password, generate_mfa_secret, get_totp_uri, verify_mfa_token
from jwt_token import create_access_token, verify_token, get_current_user, oauth2_scheme
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from schemas import DeleteUser, UserCreate, UserLogin, ForgetPassword
from GitIssues.schemas import GitLabIssue, GithubIssue
import httpx
app = FastAPI()


GITLAB_PROJECT_ID = "71108768"
GITLAB_PRIVATE_TOKEN = "glpat-3ykwnhRJE8rKrHkqJ9jE"
GITLAB_URL = "https://gitlab.com"


@app.post("/gitlab-issue")
async def create_gitlab_issue(issue: GitLabIssue):
    """
    Creates a GitLab issue using the GitLab API.
    """
    url = f"{GITLAB_URL}/api/v4/projects/{GITLAB_PROJECT_ID}/issues"
    headers = {
        "PRIVATE-TOKEN": GITLAB_PRIVATE_TOKEN,
    }
    data = {
        "title": issue.title,
        "body": issue.body,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, headers=headers, data=data)
        response.raise_for_status()
        issue_data = response.json()
        return {"message": "Issue created successfully", "issue_id": issue_data['iid']}
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request to GitLab timed out")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))