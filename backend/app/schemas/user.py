"""
User authentication schemas for request/response validation

This module contains Pydantic models for:
- User registration and login
- JWT token responses
- User profile management
- Password reset and email verification
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
import re

from app.core.security import PasswordValidator

class UserBase(BaseModel):
    """Base user model with common fields."""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.lower()

class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    password_confirm: str = Field(..., description="Password confirmation")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        is_valid, errors = PasswordValidator.validate_password(v)
        if not is_valid:
            raise ValueError(f"Password validation failed: {', '.join(errors)}")
        return v
    
    @validator('password_confirm')
    def passwords_match(cls, v, values):
        """Ensure password and confirmation match."""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

class UserResponse(UserBase):
    """Schema for user response (excludes password)."""
    id: str = Field(..., description="User ID")
    is_active: bool = Field(..., description="Whether user account is active")
    is_verified: bool = Field(False, description="Whether user email is verified")
    is_superuser: bool = Field(False, description="Whether user has admin privileges")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    """Schema for user profile updates."""
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
            return v.lower()
        return v

class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    new_password_confirm: str = Field(..., description="New password confirmation")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        is_valid, errors = PasswordValidator.validate_password(v)
        if not is_valid:
            raise ValueError(f"Password validation failed: {', '.join(errors)}")
        return v
    
    @validator('new_password_confirm')
    def passwords_match(cls, v, values):
        """Ensure new password and confirmation match."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('New passwords do not match')
        return v

class PasswordReset(BaseModel):
    """Schema for password reset request."""
    email: EmailStr = Field(..., description="User email address")

class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    new_password_confirm: str = Field(..., description="New password confirmation")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        is_valid, errors = PasswordValidator.validate_password(v)
        if not is_valid:
            raise ValueError(f"Password validation failed: {', '.join(errors)}")
        return v
    
    @validator('new_password_confirm')
    def passwords_match(cls, v, values):
        """Ensure new password and confirmation match."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('New passwords do not match')
        return v

class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")

class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str = Field(..., description="Refresh token")

class EmailVerification(BaseModel):
    """Schema for email verification."""
    token: str = Field(..., description="Email verification token")

class UserStats(BaseModel):
    """Schema for user statistics."""
    total_articles: int = Field(0, description="Total articles created")
    total_research: int = Field(0, description="Total keyword research performed")
    total_projects: int = Field(0, description="Total projects created")
    api_usage: dict = Field(default_factory=dict, description="API usage statistics")
    account_age_days: int = Field(0, description="Account age in days")

class UserProfile(UserResponse):
    """Extended user profile with statistics."""
    stats: UserStats = Field(..., description="User statistics")

# Response models
class LoginResponse(BaseModel):
    """Response model for successful login."""
    user: UserResponse = Field(..., description="User information")
    tokens: Token = Field(..., description="JWT tokens")
    message: str = Field(default="Login successful", description="Success message")

class RegisterResponse(BaseModel):
    """Response model for successful registration."""
    user: UserResponse = Field(..., description="User information")
    message: str = Field(default="Registration successful", description="Success message")
    verification_required: bool = Field(default=True, description="Whether email verification is required")

class LogoutResponse(BaseModel):
    """Response model for successful logout."""
    message: str = Field(default="Logout successful", description="Success message")

class TokenRefreshResponse(BaseModel):
    """Response model for token refresh."""
    tokens: Token = Field(..., description="New JWT tokens")
    message: str = Field(default="Token refreshed successfully", description="Success message")

# Error response models
class AuthError(BaseModel):
    """Authentication error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")

class ValidationError(BaseModel):
    """Validation error response."""
    error: str = Field(default="validation_error", description="Error type")
    message: str = Field(..., description="Error message")
    field_errors: dict = Field(..., description="Field-specific errors")

# Request context models
class AuthenticatedUser(BaseModel):
    """Current authenticated user context."""
    id: str
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    is_superuser: bool
    scopes: List[str] = Field(default_factory=list, description="User permissions/scopes")
    
    class Config:
        from_attributes = True