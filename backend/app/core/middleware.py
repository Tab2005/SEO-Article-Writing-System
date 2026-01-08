"""
Middleware components for the FastAPI application

This module provides custom middleware for:
- Request/Response logging
- Performance monitoring
- CORS handling
- Security headers
- Request ID tracking
"""

import time
import uuid
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from structlog import get_logger

from app.config import settings

logger = get_logger()

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Record start time
        start_time = time.time()
        request.state.start_time = start_time
        
        # Log incoming request
        logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            content_length=request.headers.get("content-length", 0)
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            "Request completed",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time_ms=round(process_time * 1000, 2),
            response_size=response.headers.get("content-length", 0)
        )
        
        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
        
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains" if not settings.debug else "",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        })
        
        return response

class PerformanceMiddleware(BaseHTTPMiddleware):
    """Monitor application performance metrics."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate metrics
        process_time = time.time() - start_time
        
        # Log slow requests (> 1 second)
        if process_time > 1.0:
            logger.warning(
                "Slow request detected",
                method=request.method,
                url=str(request.url),
                process_time_ms=round(process_time * 1000, 2),
                status_code=response.status_code
            )
        
        # Add performance headers for debugging
        if settings.debug:
            response.headers["X-Debug-Process-Time"] = str(round(process_time * 1000, 2))
            response.headers["X-Debug-Memory-Usage"] = "TODO"  # Can add memory usage if needed
        
        return response

def setup_middleware(app: FastAPI) -> None:
    """Configure all middleware for the FastAPI application."""
    
    # CORS middleware (should be added first)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"]
    )
    
    # Trusted host middleware (security)
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts
        )
    
    # Custom middleware (order matters - last added is executed first)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(PerformanceMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    
    logger.info(
        "Middleware configured",
        cors_origins=settings.cors_origins,
        allowed_hosts=settings.allowed_hosts,
        debug_mode=settings.debug
    )

# Health check for middleware
class HealthCheckResponse:
    """Simple health check response for monitoring."""
    
    @staticmethod
    def get_health_status() -> dict:
        """Get current application health status."""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": settings.app_version,
            "environment": "development" if settings.debug else "production",
            "services": {
                "database": "TODO",  # Will be implemented in Task 4
                "redis": "TODO",     # Will be implemented in Task 8
                "external_apis": {
                    "google_search": "TODO",  # Will be implemented in Task 5
                    "openai": "TODO"          # Will be implemented later
                }
            }
        }