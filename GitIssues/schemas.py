from pydantic import BaseModel

class GithubIssue(BaseModel):
    title: str
    body: str