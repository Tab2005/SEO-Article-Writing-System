"""
User model for authentication and user management.

This model handles:
- User registration and authentication
- Profile information
- API usage tracking
- Account status management
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from uuid import uuid4
from datetime import datetime
from typing import Optional

from app.database import Base

class User(Base):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()), index=True)
    
    # Authentication fields
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile information
    full_name = Column(String(100), nullable=True)
    company = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)
    
    # API usage tracking
    api_calls_today = Column(Integer, default=0, nullable=False)
    api_calls_month = Column(Integer, default=0, nullable=False)
    last_api_call = Column(DateTime(timezone=True), nullable=True)
    
    # Settings and preferences
    settings = Column(JSON, default=dict, nullable=False)  # User preferences
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Password recovery
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Email verification
    verification_token = Column(String(255), nullable=True)
    verification_expires = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary, optionally including sensitive data."""
        data = {
            "id": self.id,  # Already string
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "company": self.company,
            "website": self.website,
            "bio": self.bio,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_premium": self.is_premium,
            "api_calls_today": self.api_calls_today,
            "api_calls_month": self.api_calls_month,
            "last_api_call": self.last_api_call.isoformat() if self.last_api_call else None,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        
        if include_sensitive:
            data.update({
                "hashed_password": self.hashed_password,
                "password_reset_token": self.password_reset_token,
                "password_reset_expires": self.password_reset_expires.isoformat() if self.password_reset_expires else None,
                "verification_token": self.verification_token,
                "verification_expires": self.verification_expires.isoformat() if self.verification_expires else None,
            })
        
        return data
    
    @property
    def is_password_reset_valid(self) -> bool:
        """Check if password reset token is still valid."""
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        return datetime.utcnow() < self.password_reset_expires
    
    @property
    def is_verification_valid(self) -> bool:
        """Check if email verification token is still valid."""
        if not self.verification_token or not self.verification_expires:
            return False
        return datetime.utcnow() < self.verification_expires
    
    def can_make_api_call(self, daily_limit: int = 100, monthly_limit: int = 1000) -> bool:
        """Check if user can make API calls based on limits."""
        if self.is_premium:
            # Premium users have higher limits
            daily_limit *= 10
            monthly_limit *= 10
        
        return (
            self.is_active and
            self.api_calls_today < daily_limit and
            self.api_calls_month < monthly_limit
        )
    
    def increment_api_calls(self):
        """Increment API call counters."""
        self.api_calls_today += 1
        self.api_calls_month += 1
        self.last_api_call = datetime.utcnow()
    
    def reset_daily_api_calls(self):
        """Reset daily API call counter (to be called by a daily task)."""
        self.api_calls_today = 0
    
    def reset_monthly_api_calls(self):
        """Reset monthly API call counter (to be called by a monthly task)."""
        self.api_calls_month = 0