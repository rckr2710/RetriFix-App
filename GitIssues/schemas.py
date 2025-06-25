from pydantic import BaseModel

class GitLabIssue(BaseModel):
    title: str
    body: str