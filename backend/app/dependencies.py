from fastapi import Header, HTTPException

from app.config import settings


def get_client_id(x_client_id: str | None = Header(default=None)) -> str:
    if not x_client_id:
        raise HTTPException(status_code=400, detail="X-Client-Id header is required")
    return x_client_id


def require_internal_secret(x_internal_secret: str | None = Header(default=None)) -> None:
    if x_internal_secret != settings.internal_api_secret:
        raise HTTPException(status_code=401, detail="Invalid or missing internal secret")
