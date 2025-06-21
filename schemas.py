from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str
    mfa_code: str

class ForgetPassword(BaseModel):
    username: str
    new_password: str

class DeleteUser(BaseModel):
    username: str