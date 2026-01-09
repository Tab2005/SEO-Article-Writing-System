"""
Authentication API Endpoints.

Handles user registration, login, logout, and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    JWTManager,
    TokenBlacklist,
    decode_token,
)
from app.api.dependencies import get_current_active_user, oauth2_scheme
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    PasswordChange,
    Token,
)
from app.services.user_service import user_service

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user.
    
    - **email**: User's email address
    - **password**: Password (min 8 chars, must include uppercase, lowercase, digit, special char)
    - **full_name**: Optional full name
    """
    user = await user_service.create(db, user_data)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    User login.
    
    Returns access and refresh tokens.
    Use email as username.
    """
    user = await user_service.authenticate(
        db,
        email=form_data.username,
        password=form_data.password,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    # Update last login
    await user_service.update_last_login(db, user)
    
    # Generate tokens
    tokens = JWTManager.create_token_pair(user.id)
    
    return Token(**tokens)


@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
):
    """
    User logout.
    
    Invalidates the current access token.
    """
    await TokenBlacklist.add(token)
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token.
    
    Uses refresh token to generate new access token.
    """
    # Decode refresh token
    payload = decode_token(refresh_token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    
    # Check if refresh token is blacklisted
    if await TokenBlacklist.is_blacklisted(refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    # Blacklist old refresh token
    await TokenBlacklist.add(refresh_token)
    
    # Generate new token pair
    tokens = JWTManager.create_token_pair(user_id)
    
    return Token(**tokens)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current user information.
    """
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user profile.
    
    - **full_name**: New full name
    - **email**: New email (must be unique)
    """
    updated_user = await user_service.update(db, current_user, user_data)
    return updated_user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change current user's password.
    
    - **current_password**: Current password for verification
    - **new_password**: New password (must meet strength requirements)
    """
    await user_service.change_password(
        db,
        current_user,
        password_data.current_password,
        password_data.new_password,
    )
    
    return {"message": "Password changed successfully"}
