from pydantic import BaseModel


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    authenticated: bool
    token: str
    username: str
    expires_at: str
