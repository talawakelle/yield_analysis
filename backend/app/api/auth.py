from fastapi import APIRouter

from app.schemas.auth import AdminLoginRequest, AdminLoginResponse
from app.services.auth_service import (
    create_admin_session,
    destroy_session,
    require_admin,
    validate_credentials,
)
from fastapi import HTTPException, Depends, Header

router = APIRouter()


@router.post("/login", response_model=AdminLoginResponse)
def login(payload: AdminLoginRequest) -> AdminLoginResponse:
    if not validate_credentials(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    session = create_admin_session(payload.username)
    return AdminLoginResponse(
        authenticated=True,
        token=session.token,
        username=session.username,
        expires_at=session.expires_at.isoformat(),
    )


@router.get("/me")
def me(session=Depends(require_admin)) -> dict:
    return {
        "authenticated": True,
        "username": session.username,
        "expires_at": session.expires_at.isoformat(),
    }


@router.post("/logout")
def logout(authorization: str | None = Header(default=None)) -> dict:
    if authorization:
        token = authorization.split(" ", 1)[1] if authorization.lower().startswith("bearer ") else authorization
        destroy_session(token.strip())
    return {"authenticated": False}
