"""
Authentication Dependencies.

Provides FastAPI dependencies for authentication and authorization.
"""

from typing import Optional
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token, TokenBlacklist
from app.models.user import User
from app.schemas.user import TokenPayload
from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

# Development mode user ID
DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# Development mode mock user
class DevUser:
    """Mock user for development mode."""
    def __init__(self):
        self.id = DEV_USER_ID
        self.email = "dev@example.com"
        self.full_name = "開發者"
        self.is_active = True
        self.is_verified = True
        self.is_superuser = True


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Get current authenticated user from JWT token.
    
    In development mode with debug=True:
    - Accepts 'dev-access-token' as a bypass token
    - Returns DevUser for tokens with dev_user_id
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Check for missing token
    if not token:
        raise credentials_exception
    
    # Development mode bypass for literal dev-access-token
    if settings.debug and token == "dev-access-token":
        return DevUser()
    
    # Check if token is blacklisted
    try:
        if await TokenBlacklist.is_blacklisted(token):
            raise credentials_exception
    except Exception as e:
        # Redis not available in dev mode
        if settings.debug:
            print(f"[AUTH] Token blacklist check failed (dev mode): {e}")
        else:
            raise credentials_exception
    
    # Decode token
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    # Validate token type
    if payload.get("type") != "access":
        raise credentials_exception
    
    # Get user ID from token
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise credentials_exception
    
    # In dev mode, if the user ID is the dev user ID, return DevUser
    if settings.debug and user_uuid == DEV_USER_ID:
        return DevUser()
    
    # Fetch user from database
    try:
        result = await db.execute(select(User).where(User.id == user_uuid))
        user = result.scalar_one_or_none()
    except Exception as db_error:
        if settings.debug:
            print(f"[AUTH] Database error (dev mode): {db_error}")
            return DevUser()  # Return DevUser as fallback in dev mode
        raise credentials_exception
    
    if user is None:
        if settings.debug:
            print(f"[AUTH] User not found in database, returning DevUser")
            return DevUser()  # Return DevUser as fallback in dev mode
        raise credentials_exception
    
    return user


async def get_optional_current_user(
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[User]:
    """Return current user if token is present and valid, else None."""
    if not token:
        return None
    try:
        return await get_current_user(db=db, token=token)
    except HTTPException:
        # Token is invalid/expired, treat as unauthenticated
        return None


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user.
    
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get current verified user.
    
    Raises:
        HTTPException: If email is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get current superuser.
    
    Raises:
        HTTPException: If user is not superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[str]:
    """
    Get optional token for endpoints that work with or without auth.
    
    Returns:
        Token string or None
    """
    return token
