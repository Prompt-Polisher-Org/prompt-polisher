"""
dependencies.py — FastAPI dependency injection for auth.

Task: Week 3-4 / Authentication System (task.md line 146)
  [x] Create `get_current_user` dependency for protected routes

Usage in any route:
    @router.get("/protected")
    async def protected_route(current_user: User = Depends(get_current_user)):
        ...
"""
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.services.auth_service import get_user_by_id
from app.models.user import User

# HTTPBearer extracts the "Bearer <token>" from the Authorization header
bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency: Validates the JWT access token sent in the Authorization header
    and returns the corresponding User object.

    Raises 401 if the token is missing, expired, invalid, or the user
    no longer exists in the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(credentials.credentials)
        user_id: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")

        if user_id is None or token_type != "access":
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = await get_user_by_id(db, uuid.UUID(user_id))
    if user is None or not user.is_active:
        raise credentials_exception

    return user
