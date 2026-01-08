"""
Global dependencies for FastAPI application

This module provides common dependencies that can be injected into API endpoints:
- Database session management
- Authentication and authorization
- Rate limiting
- Request logging
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import time
import redis
from redis import Redis
from structlog import get_logger

from app.config import settings
from app.core.security import verify_access_token, TokenBlacklist
from app.models.user import User
from app.schemas.user import AuthenticatedUser

logger = get_logger()

# OAuth2 scheme for JWT token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login",
    auto_error=False
)

# Redis client for rate limiting and caching
redis_client: Optional[Redis] = None

async def get_redis() -> Redis:
    """Get Redis client instance."""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client

class RateLimiter:
    """Rate limiting dependency using Redis."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    async def __call__(self, request: Request):
        """Check rate limit for the requesting client."""
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Create Redis key
        current_time = int(time.time())
        window_start = current_time - (current_time % self.window_seconds)
        redis_key = f"rate_limit:{client_ip}:{window_start}"
        
        try:
            redis_client = await get_redis()
            
            # Increment request count
            current_requests = redis_client.incr(redis_key)
            
            # Set expiration for the first request in this window
            if current_requests == 1:
                redis_client.expire(redis_key, self.window_seconds)
            
            # Check if rate limit exceeded
            if current_requests > self.max_requests:
                logger.warning(
                    "Rate limit exceeded",
                    client_ip=client_ip,
                    current_requests=current_requests,
                    max_requests=self.max_requests
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "max_requests": self.max_requests,
                        "window_seconds": self.window_seconds,
                        "reset_time": window_start + self.window_seconds
                    }
                )
        
        except redis.RedisError as e:
            logger.error("Redis error in rate limiting", error=str(e))
            # Continue without rate limiting if Redis is unavailable
            pass
        
        return True

# Rate limiting instances for different endpoints
rate_limit_general = RateLimiter(max_requests=100, window_seconds=3600)  # 100/hour
rate_limit_auth = RateLimiter(max_requests=10, window_seconds=900)       # 10/15min
rate_limit_research = RateLimiter(max_requests=20, window_seconds=3600)   # 20/hour

# Convenience function for research endpoints
async def rate_limit_check(request: Request) -> bool:
    """Rate limit check for research endpoints."""
    return await rate_limit_research(request)

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[AuthenticatedUser]:
    """
    Get current authenticated user from JWT token.
    
    Returns:
        AuthenticatedUser if token is valid, None for anonymous access
    """
    if not token:
        return None  # Allow anonymous access
    
    try:
        # Verify JWT token
        payload = verify_access_token(token)
        if not payload:
            return None
            
        # Check if token is blacklisted
        if await TokenBlacklist.is_token_blacklisted(token):
            return None
            
        # Extract user information from token
        user_id = payload.get("sub")
        if not user_id:
            return None
            
        # For now, create AuthenticatedUser from payload
        # In production, you'd fetch from database
        user_data = {
            "id": user_id,
            "email": payload.get("email", "unknown@example.com"),
            "username": payload.get("username", "unknown"),
            "full_name": payload.get("full_name"),
            "is_active": payload.get("is_active", True),
            "is_verified": payload.get("is_verified", False),
            "is_superuser": payload.get("is_superuser", False),
            "scopes": payload.get("scopes", [])
        }
        
        return AuthenticatedUser(**user_data)
        
    except Exception as e:
        logger.warning("Failed to get current user", error=str(e))
        return None

async def get_current_active_user(current_user: Optional[AuthenticatedUser] = Depends(get_current_user)) -> AuthenticatedUser:
    """Get current active user (requires authentication)."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    
    return current_user

async def get_current_superuser(current_user: AuthenticatedUser = Depends(get_current_active_user)) -> AuthenticatedUser:
    """Get current active superuser (requires admin privileges)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user

async def get_verified_user(current_user: AuthenticatedUser = Depends(get_current_active_user)) -> AuthenticatedUser:
    """Get current verified user (requires email verification)."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    
    return current_user

async def get_db_session() -> AsyncSession:
    """
    Get database session.
    
    TODO: Implement in Task 4 (Database Configuration)
    """
    # Placeholder implementation
    # async with AsyncSessionLocal() as session:
    #     try:
    #         yield session
    #     finally:
    #         await session.close()
    
    # For now, return a mock session
    class MockSession:
        async def close(self):
            pass
    
    return MockSession()

async def log_request(request: Request):
    """Log incoming requests for debugging and monitoring."""
    start_time = time.time()
    
    logger.info(
        "Incoming request",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown")
    )
    
    # Store start time for response time calculation
    request.state.start_time = start_time
    return True

class RequestValidator:
    """Validate common request parameters."""
    
    @staticmethod
    async def validate_keyword(keyword: str) -> str:
        """Validate keyword parameter."""
        if not keyword or len(keyword.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Keyword cannot be empty"
            )
        
        if len(keyword) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Keyword too long (max 100 characters)"
            )
        
        return keyword.strip()
    
    @staticmethod
    async def validate_pagination(skip: int = 0, limit: int = 100) -> tuple[int, int]:
        """Validate pagination parameters."""
        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skip must be >= 0"
            )
        
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )
        
        return skip, limit