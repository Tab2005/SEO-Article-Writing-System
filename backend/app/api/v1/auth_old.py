"""
User Authentication API endpoints

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
    """
    註冊新使用者
    
    創建新的使用者帳號：
    - 驗證使用者資料
    - 檢查 email 和 username 唯一性
    - 建立使用者帳號
    - 發送驗證郵件 (background task)
    """
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
        
        # TODO: Add background task for email verification
        # background_tasks.add_task(send_verification_email, new_user.email)
        
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
    """
    使用者登入
    
    驗證使用者憑證並返回 JWT token：
    - 驗證 email/password
    - 檢查帳號狀態
    - 生成 access 和 refresh token
    - 更新登入時間
    """
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
            "scopes": []  # TODO: Add user scopes/permissions
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

@router.post("/refresh", response_model=dict)
async def refresh_token(token: dict):
    """
    刷新 access token
    
    TODO: 實作 token 刷新邏輯
    - 驗證 refresh token
    - 生成新的 access token
    """
    return {"message": "Token refresh endpoint - TODO: implement"}

@router.get("/me", response_model=dict)
async def get_current_user():
    """
    獲取當前用戶資訊
    
    TODO: 實作獲取當前用戶邏輯
    - 從 JWT token 中解析用戶資訊
    - 返回用戶詳細資料
    """
    return {"message": "Get current user endpoint - TODO: implement"}

@router.post("/logout", response_model=dict)
async def logout():
    """
    用戶登出
    
    TODO: 實作登出邏輯
    - 將 token 加入黑名單
    - 清除用戶 session
    """
    return {"message": "User logout endpoint - TODO: implement"}