"""
Authentication API Endpoints.

Handles user registration, login (email + Google OAuth), logout, and token management.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    JWTManager,
    TokenBlacklist,
    decode_token,
    get_password_hash,
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
from app.services.google_oauth import google_oauth_service

router = APIRouter()


class GoogleLoginRequest(BaseModel):
    """Request schema for Google login."""
    access_token: str


class GoogleLoginResponse(BaseModel):
    """Response schema for Google login with user info."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict  # User info from Google


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
    User login with email/password.
    
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


@router.post("/google", response_model=GoogleLoginResponse)
async def google_login(
    request: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Login with Google OAuth.
    
    - **access_token**: Google OAuth access token obtained from frontend
    
    Creates a new user if first time login, otherwise returns tokens for existing user.
    """
    from app.config import settings
    import uuid
    
    print("=" * 50)
    print("[AUTH] Google login request received")
    print(f"[AUTH] Access token length: {len(request.access_token)}")
    
    try:
        # Verify Google token and get user info
        print("[AUTH] Verifying Google token...")
        google_user = await google_oauth_service.verify_google_token(request.access_token)
        print(f"[AUTH] Google user: {google_user.get('email')}")
        
        if not google_user.get("verified_email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google email not verified",
            )
        
        email = google_user.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Google",
            )
        
        # Try database operations
        try:
            # Check if user exists
            user = await user_service.get_by_email(db, email)
            
            if not user:
                # Create new user with Google info
                import secrets
                random_password = secrets.token_urlsafe(32)
                
                user = User(
                    email=email.lower(),
                    hashed_password=get_password_hash(random_password),
                    full_name=google_user.get("name"),
                    is_verified=True,  # Google already verified email
                    is_active=True,
                )
                db.add(user)
                await db.flush()
                await db.refresh(user)
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Inactive user",
                )
            
            # Update last login
            await user_service.update_last_login(db, user)
            
            # Generate tokens
            tokens = JWTManager.create_token_pair(user.id)
            
        except Exception as db_error:
            # Database error - if in debug mode, create dev token
            if settings.debug:
                print(f"Database error (dev mode bypass): {db_error}")
                # Generate token for dev user
                dev_user_id = str(uuid.UUID("00000000-0000-0000-0000-000000000001"))
                tokens = JWTManager.create_token_pair(dev_user_id)
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database error: {str(db_error)}",
                )
        
        return GoogleLoginResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            user={
                "id": str(google_user.get("google_id", "")),
                "email": email,
                "full_name": google_user.get("name", ""),
                "is_verified": True,
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Google OAuth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google login failed: {str(e)}",
        )


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
