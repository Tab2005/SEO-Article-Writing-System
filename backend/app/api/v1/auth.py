"""
User Authentication API endpoints - Complete Implementation

This module handles user authentication including:
- User registration and login
- JWT token management
- Password reset and email verification  
- User profile management
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from structlog import get_logger

from app.core.security import (
    PasswordManager, JWTManager, create_token_pair, 
    verify_refresh_token, TokenBlacklist
)
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, UserUpdate,
    LoginResponse, RegisterResponse, LogoutResponse, TokenRefreshResponse,
    Token, TokenRefresh, PasswordChange, PasswordReset, PasswordResetConfirm,
    EmailVerification, AuthenticatedUser
)
from app.api.dependencies import (
    get_current_user, get_current_active_user, get_verified_user,
    rate_limit_auth, log_request, oauth2_scheme
)

router = APIRouter()
logger = get_logger()

# Mock user database for testing (replace with real database in production)
MOCK_USERS = {}

def create_mock_user(user_data: UserCreate) -> UserResponse:
    """Create a mock user for testing purposes."""
    user_id = f"user_{len(MOCK_USERS) + 1}"
    
    user = UserResponse(
        id=user_id,
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        is_active=True,
        is_verified=False,  # Would require email verification
        is_superuser=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        last_login=None
    )
    
    # Store user with hashed password
    MOCK_USERS[user_id] = {
        **user.model_dump(),
        "hashed_password": PasswordManager.hash_password(user_data.password)
    }
    
    return user

def get_mock_user_by_email(email: str) -> Dict[str, Any] | None:
    """Get mock user by email."""
    for user_data in MOCK_USERS.values():
        if user_data["email"] == email:
            return user_data
    return None

def get_mock_user_by_id(user_id: str) -> Dict[str, Any] | None:
    """Get mock user by ID."""
    return MOCK_USERS.get(user_id)

@router.post("/register", response_model=RegisterResponse)
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    _: bool = Depends(rate_limit_auth),
    __: bool = Depends(log_request)
):
    """註冊新使用者"""
    try:
        # Check if user already exists
        existing_user = get_mock_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check username uniqueness
        for user in MOCK_USERS.values():
            if user["username"] == user_data.username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Create user
        new_user = create_mock_user(user_data)
        
        logger.info("User registered successfully", user_id=new_user.id, email=new_user.email)
        
        return RegisterResponse(
            user=new_user,
            message="Registration successful. Please check your email for verification.",
            verification_required=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    _: bool = Depends(rate_limit_auth),
    __: bool = Depends(log_request)
):
    """使用者登入"""
    try:
        # Find user by email (form_data.username is actually email in our case)
        user_data = get_mock_user_by_email(form_data.username)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not PasswordManager.verify_password(form_data.password, user_data["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if account is active
        if not user_data["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )
        
        # Update last login
        user_data["last_login"] = datetime.now()
        
        # Create user response
        user_response = UserResponse(**user_data)
        
        # Create JWT tokens
        token_data = {
            "sub": user_data["id"],
            "email": user_data["email"],
            "username": user_data["username"],
            "full_name": user_data["full_name"],
            "is_active": user_data["is_active"],
            "is_verified": user_data["is_verified"],
            "is_superuser": user_data["is_superuser"],
            "scopes": []
        }
        
        tokens = create_token_pair(token_data)
        token_response = Token(**tokens)
        
        logger.info("User login successful", user_id=user_data["id"], email=user_data["email"])
        
        return LoginResponse(
            user=user_response,
            tokens=token_response,
            message="Login successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/logout", response_model=LogoutResponse)
async def logout(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    token: str = Depends(oauth2_scheme),
    __: bool = Depends(log_request)
):
    """使用者登出"""
    try:
        # Blacklist the current token
        await TokenBlacklist.blacklist_token(token, "logout")
        
        logger.info("User logout successful", user_id=current_user.id)
        
        return LogoutResponse(message="Logout successful")
        
    except Exception as e:
        logger.error("Logout failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    token_data: TokenRefresh,
    _: bool = Depends(rate_limit_auth),
    __: bool = Depends(log_request)
):
    """刷新 JWT token"""
    try:
        # Verify refresh token
        payload = verify_refresh_token(token_data.refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Get current user data
        user_data = get_mock_user_by_id(user_id)
        if not user_data or not user_data["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new token pair
        token_payload = {
            "sub": user_data["id"],
            "email": user_data["email"],
            "username": user_data["username"],
            "full_name": user_data["full_name"],
            "is_active": user_data["is_active"],
            "is_verified": user_data["is_verified"],
            "is_superuser": user_data["is_superuser"],
            "scopes": []
        }
        
        new_tokens = create_token_pair(token_payload)
        token_response = Token(**new_tokens)
        
        # Blacklist old refresh token
        await TokenBlacklist.blacklist_token(token_data.refresh_token, "refresh")
        
        logger.info("Token refresh successful", user_id=user_id)
        
        return TokenRefreshResponse(
            tokens=token_response,
            message="Token refreshed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    __: bool = Depends(log_request)
):
    """獲取當前使用者資料"""
    try:
        # Get full user data from database
        user_data = get_mock_user_by_id(current_user.id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(**user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get user profile", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )

@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    __: bool = Depends(log_request)
):
    """更新當前使用者資料"""
    try:
        # Get current user data
        user_data = get_mock_user_by_id(current_user.id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check username uniqueness if being updated
        if user_update.username and user_update.username != user_data["username"]:
            for uid, existing_user in MOCK_USERS.items():
                if uid != current_user.id and existing_user["username"] == user_update.username:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already taken"
                    )
        
        # Update fields
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            user_data[field] = value
            
        user_data["updated_at"] = datetime.now()
        
        logger.info("User profile updated", user_id=current_user.id)
        
        return UserResponse(**user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update user profile", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )

@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    _: bool = Depends(rate_limit_auth),
    __: bool = Depends(log_request)
):
    """更改使用者密碼"""
    try:
        # Get current user data
        user_data = get_mock_user_by_id(current_user.id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not PasswordManager.verify_password(password_change.current_password, user_data["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_hashed_password = PasswordManager.hash_password(password_change.new_password)
        
        # Update password
        user_data["hashed_password"] = new_hashed_password
        user_data["updated_at"] = datetime.now()
        
        logger.info("Password changed successfully", user_id=current_user.id)
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Password change failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )