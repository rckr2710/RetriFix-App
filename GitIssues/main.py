from typing import Optional
from fastapi import Cookie, FastAPI, Depends, File, Form, HTTPException, Security, UploadFile, requests
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
async def create_gitlab_issue(title: str = Form(...),
    description: str = Form(...),username: str = Cookie(None),image: Optional[UploadFile] = File(None),get_current_user: str = Depends(get_current_user)):

    url = f"{GITLAB_URL}/api/v4/projects/{GITLAB_PROJECT_ID}/issues"
    headers = {
        "PRIVATE-TOKEN": GITLAB_PRIVATE_TOKEN,
    }
    image_markdown = ""
    if image:
        contents = await image.read()
        files = {"file": (image.filename, contents, image.content_type)}
        async with httpx.AsyncClient(timeout=10) as client:
            upload_url = f"{GITLAB_URL}/api/v4/projects/{GITLAB_PROJECT_ID}/uploads"
            upload_resp = await client.post(upload_url, headers=headers, files=files)
            if upload_resp.status_code != 201:
                raise HTTPException(status_code=upload_resp.status_code, detail=upload_resp.text)
            upload_data = upload_resp.json()
            image_url = upload_data["url"]
            image_markdown = f"\n\n![{upload_data['alt']}]({GITLAB_URL}{image_url})"

    data = {
        "title": title,
        "description": f"{description}{image_markdown}",
        "labels": "support",
        "author" : {
            "username" : username
        }
        # we need to add list of assignee_ids, for different issues, it should alter
        # "assignee_ids": [1],
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
    

@app.delete("/gitlab-issue/{issue_id}")
def delete_gitlab_issue(issue_id: int, get_current_user: str = Depends(get_current_user)):
    if not issue_id:
        raise HTTPException(status_code=400, detail="Issue ID is required")
    url = f"{GITLAB_URL}/api/v4/projects/{GITLAB_PROJECT_ID}/issues/{issue_id}"
    headers = {
        "PRIVATE-TOKEN": GITLAB_PRIVATE_TOKEN,
    }
    try:
        response = httpx.delete(url, headers=headers)
        response.raise_for_status()
        return {"message": "Issue deleted successfully"}
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request to GitLab timed out")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.put("/gitlab-issue/close-issue/{issue_id}")
def close_gitlab_issue(issue_id: int, get_current_user: str = Depends(get_current_user)):
    if not issue_id:
        raise HTTPException(status_code=400, detail="Issue ID is required")
    url = f"{GITLAB_URL}/api/v4/projects/{GITLAB_PROJECT_ID}/issues/{issue_id}"
    headers = {
        "PRIVATE-TOKEN": GITLAB_PRIVATE_TOKEN,
    }
    data = {
        "state_event": "close"
    }
    try:
        response = httpx.put(url, headers=headers, data=data)
        response.raise_for_status()
        return {"message": "Issue closed successfully"}
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request to GitLab timed out")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.put("/gitlab-issue/edit-issue/{issue_id}")
async def edit_gitlab_issue(issue_id: int, title: str = Form(...), description: str = Form(...),image: Optional[UploadFile] = File(None) , get_current_user: str = Depends(get_current_user)):
    if not issue_id:
        raise HTTPException(status_code=400, detail="Issue ID is required")
    url = f"{GITLAB_URL}/api/v4/projects/{GITLAB_PROJECT_ID}/issues/{issue_id}"
    headers = {
        "PRIVATE-TOKEN": GITLAB_PRIVATE_TOKEN,
    }
    image_markdown = ""
    if image:
        contents = await image.read()
        files = {"file": (image.filename, contents, image.content_type)}
        async with httpx.AsyncClient(timeout=10) as client:
            upload_url = f"{GITLAB_URL}/api/v4/projects/{GITLAB_PROJECT_ID}/uploads"
            upload_resp = await client.post(upload_url, headers=headers, files=files)
            if upload_resp.status_code != 201:
                raise HTTPException(status_code=upload_resp.status_code, detail=upload_resp.text)
            upload_data = upload_resp.json()
            image_url = upload_data["url"]
            image_markdown = f"\n\n![{upload_data['alt']}]({GITLAB_URL}{image_url})"
    data = {
        "title": title,
        "description": f"{description}{image_markdown}",
        "type" : "ISSUE"
    }
    try:
        response = httpx.put(url, headers=headers, data=data)
        response.raise_for_status()
        return {"message": "Issue updated successfully"}
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request to GitLab timed out")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))    
