from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredential
from app.utils.security import decode_token
from app.utils.errors import InvalidTokenError
from typing import Optional, Dict, Any

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthCredential = Depends(security),
) -> Dict[str, Any]:
    """
    Validate JWT token from Authorization header.
    Returns decoded token payload with user_id and tenant_id.
    """
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")

    if not user_id or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing required claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"user_id": user_id, "tenant_id": tenant_id}


async def get_optional_user(
    credentials: Optional[HTTPAuthCredential] = Depends(security),
) -> Optional[Dict[str, Any]]:
    """
    Optionally validate JWT token. Returns None if no token provided.
    """
    if credentials is None:
        return None

    return await get_current_user(credentials)
