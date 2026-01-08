"""
Custom exceptions for the SEO Article Writing System

This module defines custom exception classes and error handling logic
for different types of errors that can occur in the application.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from structlog import get_logger

logger = get_logger()

class SEOSystemException(Exception):
    """Base exception class for all system-specific errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or "SYSTEM_ERROR"
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(SEOSystemException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details
        )

class AuthenticationError(SEOSystemException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR"
        )

class AuthorizationError(SEOSystemException):
    """Raised when user lacks required permissions."""
    
    def __init__(self, message: str = "Insufficient permissions", required_permission: Optional[str] = None):
        details = {}
        if required_permission:
            details["required_permission"] = required_permission
        
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=details
        )

class ExternalAPIError(SEOSystemException):
    """Raised when external API calls fail."""
    
    def __init__(
        self,
        message: str,
        service: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None
    ):
        details = {
            "service": service,
            "status_code": status_code,
            "response_body": response_body
        }
        
        super().__init__(
            message=message,
            error_code="EXTERNAL_API_ERROR",
            details=details
        )

class DatabaseError(SEOSystemException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        details = {}
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details
        )

class RateLimitError(SEOSystemException):
    """Raised when rate limits are exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: Optional[int] = None,
        window_seconds: Optional[int] = None,
        reset_time: Optional[int] = None
    ):
        details = {
            "limit": limit,
            "window_seconds": window_seconds,
            "reset_time": reset_time
        }
        
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details=details
        )

class CrawlerError(SEOSystemException):
    """Raised when web crawling operations fail."""
    
    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        details = {
            "url": url,
            "status_code": status_code
        }
        
        super().__init__(
            message=message,
            error_code="CRAWLER_ERROR",
            details=details
        )

class ContentGenerationError(SEOSystemException):
    """Raised when AI content generation fails."""
    
    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        token_count: Optional[int] = None
    ):
        details = {
            "model": model,
            "token_count": token_count
        }
        
        super().__init__(
            message=message,
            error_code="CONTENT_GENERATION_ERROR",
            details=details
        )

# Exception handlers for FastAPI

async def seo_system_exception_handler(request: Request, exc: SEOSystemException) -> JSONResponse:
    """Handle all custom SEO system exceptions."""
    
    logger.error(
        "SEO system exception",
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        url=str(request.url),
        method=request.method
    )
    
    # Map error codes to HTTP status codes
    status_code_mapping = {
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "AUTHENTICATION_ERROR": status.HTTP_401_UNAUTHORIZED,
        "AUTHORIZATION_ERROR": status.HTTP_403_FORBIDDEN,
        "RATE_LIMIT_ERROR": status.HTTP_429_TOO_MANY_REQUESTS,
        "EXTERNAL_API_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
        "DATABASE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "CRAWLER_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "CONTENT_GENERATION_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "SYSTEM_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    http_status = status_code_mapping.get(exc.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return JSONResponse(
        status_code=http_status,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            },
            "timestamp": str(request.state.start_time) if hasattr(request.state, 'start_time') else None,
            "path": str(request.url.path)
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions."""
    
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url),
        method=request.method
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "details": {}
            },
            "timestamp": str(request.state.start_time) if hasattr(request.state, 'start_time') else None,
            "path": str(request.url.path)
        }
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other unhandled exceptions."""
    
    logger.error(
        "Unhandled exception",
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        url=str(request.url),
        method=request.method,
        exc_info=exc
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {
                    "type": type(exc).__name__
                }
            },
            "timestamp": str(request.state.start_time) if hasattr(request.state, 'start_time') else None,
            "path": str(request.url.path)
        }
    )