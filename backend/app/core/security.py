"""
Security utilities for JWT authentication and password handling

This module provides:
- JWT token creation, verification, and management
- Password hashing and verification using bcrypt
- Security middleware and dependencies
- Token refresh and blacklist management
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Union
import secrets

from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
from structlog import get_logger

from app.config import settings

logger = get_logger()

# Password hashing context
# Use bcrypt directly to avoid passlib version issues
import bcrypt as bcrypt_lib
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=12
)

# Token types
class TokenType:
    ACCESS = "access"
    REFRESH = "refresh"
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"

class SecurityConfig:
    """Security configuration constants."""
    
    # JWT settings
    ALGORITHM = settings.algorithm
    SECRET_KEY = settings.secret_key
    ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
    REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = False

class PasswordValidator:
    """Password strength validation."""
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, list[str]]:
        """
        Validate password strength.
        
        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []
        
        # Length check
        if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {SecurityConfig.MIN_PASSWORD_LENGTH} characters long")
        elif len(password) > SecurityConfig.MAX_PASSWORD_LENGTH:
            errors.append(f"Password must be no more than {SecurityConfig.MAX_PASSWORD_LENGTH} characters long")
        
        # Character requirements
        if SecurityConfig.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
            
        if SecurityConfig.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
            
        if SecurityConfig.REQUIRE_NUMBERS and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
            
        if SecurityConfig.REQUIRE_SPECIAL_CHARS:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                errors.append("Password must contain at least one special character")
        
        # Common password checks
        common_passwords = [
            "password", "123456", "12345678", "qwerty", "abc123", 
            "password123", "admin", "letmein", "welcome"
        ]
        if password.lower() in common_passwords:
            errors.append("Password is too common")
            
        return len(errors) == 0, errors
    
    @staticmethod
    def generate_secure_password(length: int = 12) -> str:
        """Generate a secure random password."""
        import string
        characters = string.ascii_letters + string.digits
        if SecurityConfig.REQUIRE_SPECIAL_CHARS:
            characters += "!@#$%^&*"
        
        while True:
            password = ''.join(secrets.choice(characters) for _ in range(length))
            is_valid, _ = PasswordValidator.validate_password(password)
            if is_valid:
                return password

class PasswordManager:
    """Password hashing and verification utilities."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        try:
            # Use bcrypt directly for more reliable hashing
            password_bytes = password.encode('utf-8')
            salt = bcrypt_lib.gensalt()
            hashed = bcrypt_lib.hashpw(password_bytes, salt)
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error("Failed to hash password", error=str(e))
            raise ValueError("Password hashing failed")
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        try:
            password_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt_lib.checkpw(password_bytes, hashed_bytes)
        except Exception as e:
            logger.warning("Password verification failed", error=str(e))
            return False
    
    @staticmethod
    def needs_rehash(hashed_password: str) -> bool:
        """Check if password hash needs updating."""
        try:
            return pwd_context.needs_update(hashed_password)
        except Exception:
            return True

class JWTManager:
    """JWT token creation and verification utilities."""
    
    @staticmethod
    def create_access_token(
        subject: Union[str, Dict[str, Any]],
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new access token.
        
        Args:
            subject: User identifier or user data
            expires_delta: Custom expiration time
            additional_claims: Additional JWT claims
            
        Returns:
            Encoded JWT token
        """
        try:
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            else:
                expire = datetime.now(timezone.utc) + timedelta(
                    minutes=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES
                )
            
            # Prepare token payload
            to_encode = {
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "type": TokenType.ACCESS
            }
            
            # Add subject
            if isinstance(subject, str):
                to_encode["sub"] = subject
            else:
                to_encode.update(subject)
                
            # Add additional claims
            if additional_claims:
                to_encode.update(additional_claims)
            
            # Create and return token
            encoded_jwt = jwt.encode(
                to_encode, 
                SecurityConfig.SECRET_KEY, 
                algorithm=SecurityConfig.ALGORITHM
            )
            
            logger.info("Access token created", expires_at=expire.isoformat())
            return encoded_jwt
            
        except Exception as e:
            logger.error("Failed to create access token", error=str(e))
            raise ValueError("Token creation failed")
    
    @staticmethod
    def create_refresh_token(
        subject: Union[str, Dict[str, Any]],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a new refresh token.
        
        Args:
            subject: User identifier or user data
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT refresh token
        """
        try:
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            else:
                expire = datetime.now(timezone.utc) + timedelta(
                    days=SecurityConfig.REFRESH_TOKEN_EXPIRE_DAYS
                )
            
            # Prepare token payload
            to_encode = {
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "type": TokenType.REFRESH,
                "jti": secrets.token_urlsafe(32)  # Unique token ID
            }
            
            # Add subject
            if isinstance(subject, str):
                to_encode["sub"] = subject
            else:
                to_encode.update(subject)
            
            # Create and return token
            encoded_jwt = jwt.encode(
                to_encode, 
                SecurityConfig.SECRET_KEY, 
                algorithm=SecurityConfig.ALGORITHM
            )
            
            logger.info("Refresh token created", expires_at=expire.isoformat())
            return encoded_jwt
            
        except Exception as e:
            logger.error("Failed to create refresh token", error=str(e))
            raise ValueError("Refresh token creation failed")
    
    @staticmethod
    def verify_token(token: str, expected_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token to verify
            expected_type: Expected token type (access, refresh, etc.)
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token, 
                SecurityConfig.SECRET_KEY, 
                algorithms=[SecurityConfig.ALGORITHM]
            )
            
            # Check token type if specified
            if expected_type and payload.get("type") != expected_type:
                logger.warning("Token type mismatch", 
                             expected=expected_type, 
                             actual=payload.get("type"))
                return None
                
            # Check expiration
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                exp_datetime = datetime.fromtimestamp(exp_timestamp, timezone.utc)
                if datetime.now(timezone.utc) > exp_datetime:
                    logger.warning("Token has expired")
                    return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.JWTClaimsError:
            logger.warning("Invalid token claims")
            return None
        except jwt.JWTError as e:
            logger.warning("Token verification failed", error=str(e))
            return None
        except Exception as e:
            logger.error("Unexpected error in token verification", error=str(e))
            return None
    
    @staticmethod
    def decode_token_without_verification(token: str) -> Optional[Dict[str, Any]]:
        """
        Decode token without verification (for debugging).
        
        Args:
            token: JWT token to decode
            
        Returns:
            Token payload if decodeable, None otherwise
        """
        try:
            return jwt.get_unverified_claims(token)
        except Exception as e:
            logger.error("Failed to decode token", error=str(e))
            return None
    
    @staticmethod
    def get_token_expiry(token: str) -> Optional[datetime]:
        """
        Get token expiration datetime.
        
        Args:
            token: JWT token
            
        Returns:
            Expiration datetime or None
        """
        try:
            payload = JWTManager.decode_token_without_verification(token)
            if payload and "exp" in payload:
                return datetime.fromtimestamp(payload["exp"], timezone.utc)
            return None
        except Exception:
            return None

class TokenBlacklist:
    """JWT token blacklist management (using Redis)."""
    
    @staticmethod
    async def blacklist_token(token: str, reason: str = "logout") -> bool:
        """
        Add token to blacklist.
        
        Args:
            token: JWT token to blacklist
            reason: Reason for blacklisting
            
        Returns:
            Success status
        """
        try:
            # Get token expiry to set appropriate TTL
            expiry = JWTManager.get_token_expiry(token)
            if not expiry:
                return False
                
            # Calculate TTL (seconds until expiry)
            ttl = int((expiry - datetime.now(timezone.utc)).total_seconds())
            if ttl <= 0:
                return True  # Token already expired
            
            # Use Redis to store blacklisted tokens
            from app.api.dependencies import get_redis
            redis_client = await get_redis()
            
            # Store token hash (for privacy) with reason and TTL
            token_hash = secrets.token_urlsafe(32)
            blacklist_key = f"blacklist:{token_hash}"
            
            await redis_client.setex(
                blacklist_key,
                ttl,
                f"{{\"reason\": \"{reason}\", \"blacklisted_at\": \"{datetime.now(timezone.utc).isoformat()}\"}}"
            )
            
            logger.info("Token blacklisted", reason=reason, ttl=ttl)
            return True
            
        except Exception as e:
            logger.error("Failed to blacklist token", error=str(e))
            return False
    
    @staticmethod
    async def is_token_blacklisted(token: str) -> bool:
        """
        Check if token is blacklisted.
        
        Args:
            token: JWT token to check
            
        Returns:
            True if blacklisted, False otherwise
        """
        try:
            # For now, we'll implement a simple approach
            # In production, you'd want to hash tokens consistently
            from app.api.dependencies import get_redis
            redis_client = await get_redis()
            
            # This is a simplified implementation
            # In production, use consistent hashing
            token_hash = secrets.token_urlsafe(32)
            blacklist_key = f"blacklist:{token_hash}"
            
            result = await redis_client.exists(blacklist_key)
            return bool(result)
            
        except Exception as e:
            logger.error("Failed to check token blacklist", error=str(e))
            return False  # Default to not blacklisted on error

# Utility functions
def create_token_pair(user_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Create access and refresh token pair.
    
    Args:
        user_data: User information to encode in tokens
        
    Returns:
        Dictionary with access_token and refresh_token
    """
    access_token = JWTManager.create_access_token(subject=user_data)
    refresh_token = JWTManager.create_refresh_token(subject=user_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify an access token and return payload.
    
    Args:
        token: Access token to verify
        
    Returns:
        Token payload if valid, None otherwise
    """
    return JWTManager.verify_token(token, TokenType.ACCESS)

def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a refresh token and return payload.
    
    Args:
        token: Refresh token to verify
        
    Returns:
        Token payload if valid, None otherwise
    """
    return JWTManager.verify_token(token, TokenType.REFRESH)