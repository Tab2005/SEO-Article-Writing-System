"""
Security Module.

Handles password hashing, JWT token management, and authentication utilities.
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import uuid

from passlib.context import CryptContext
from jose import jwt, JWTError

from app.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordValidator:
    """Validates password strength requirements."""
    
    MIN_LENGTH = 8
    
    @classmethod
    def validate(cls, password: str) -> tuple[bool, list[str]]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters")
        
        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors


class PasswordManager:
    """Manages password hashing and verification."""
    
    @staticmethod
    def hash(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)


class JWTManager:
    """Manages JWT token creation and verification."""
    
    @staticmethod
    def create_access_token(
        subject: str | uuid.UUID,
        expires_delta: Optional[timedelta] = None,
        extra_claims: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Create an access token.
        
        Args:
            subject: Token subject (usually user ID)
            expires_delta: Custom expiration time
            extra_claims: Additional claims to include
            
        Returns:
            Encoded JWT token
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.access_token_expire_minutes
            )
        
        to_encode = {
            "sub": str(subject),
            "exp": expire,
            "type": "access",
            "iat": datetime.now(timezone.utc),
        }
        
        if extra_claims:
            to_encode.update(extra_claims)
        
        return jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm,
        )
    
    @staticmethod
    def create_refresh_token(
        subject: str | uuid.UUID,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a refresh token.
        
        Args:
            subject: Token subject (usually user ID)
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT refresh token
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=settings.refresh_token_expire_days
            )
        
        to_encode = {
            "sub": str(subject),
            "exp": expire,
            "type": "refresh",
            "iat": datetime.now(timezone.utc),
        }
        
        return jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm,
        )
    
    @staticmethod
    def decode_token(token: str) -> Optional[dict[str, Any]]:
        """
        Decode and verify a JWT token.
        
        Args:
            token: JWT token to decode
            
        Returns:
            Token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm],
            )
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def create_token_pair(subject: str | uuid.UUID) -> dict[str, str]:
        """
        Create both access and refresh tokens.
        
        Args:
            subject: Token subject (usually user ID)
            
        Returns:
            Dict with access_token, refresh_token, and token_type
        """
        return {
            "access_token": JWTManager.create_access_token(subject),
            "refresh_token": JWTManager.create_refresh_token(subject),
            "token_type": "bearer",
        }


class TokenBlacklist:
    """
    Token blacklist for logout functionality.
    
    Uses Redis for storage (to be integrated with cache_manager).
    For now, uses in-memory storage as fallback.
    """
    
    _blacklist: set[str] = set()
    
    @classmethod
    async def add(cls, token: str) -> None:
        """Add token to blacklist."""
        # TODO: Use Redis in production
        cls._blacklist.add(token)
    
    @classmethod
    async def is_blacklisted(cls, token: str) -> bool:
        """Check if token is blacklisted."""
        return token in cls._blacklist
    
    @classmethod
    async def clear(cls) -> None:
        """Clear all blacklisted tokens."""
        cls._blacklist.clear()


# Convenience functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return PasswordManager.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return PasswordManager.hash(password)


def create_access_token(subject: str | uuid.UUID, **kwargs) -> str:
    """Create an access token."""
    return JWTManager.create_access_token(subject, **kwargs)


def create_refresh_token(subject: str | uuid.UUID, **kwargs) -> str:
    """Create a refresh token."""
    return JWTManager.create_refresh_token(subject, **kwargs)


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """Decode a JWT token."""
    return JWTManager.decode_token(token)
