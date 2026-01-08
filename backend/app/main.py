"""
SEO Article Writing System - FastAPI Application Entry Point

This is the main entry point for the FastAPI application.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.core.middleware import setup_middleware, HealthCheckResponse
from app.core.exceptions import (
    SEOSystemException,
    seo_system_exception_handler,
    http_exception_handler,
    general_exception_handler
)

# 將在後續任務中添加路由導入
# from app.api.v1 import auth, research, content

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("🚀 SEO Article Writing System starting up...")
    print(f"📊 Configuration loaded - Debug: {settings.debug}")
    print(f"🌐 CORS Origins: {settings.cors_origins}")
    
    # TODO: Initialize database connection pool
    # TODO: Initialize Redis connection
    # TODO: Verify external API credentials
    
    yield
    
    # Shutdown
    print("📴 SEO Article Writing System shutting down...")
    # TODO: Close database connections
    # TODO: Close Redis connections

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="SEO Article Writing System API",
        description="AI-powered SEO article writing and research platform",
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,  # Disable docs in production
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
        debug=settings.debug
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Setup exception handlers
    app.add_exception_handler(SEOSystemException, seo_system_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    # Health check endpoints
    @app.get("/")
    async def root():
        """Root endpoint for basic health check."""
        return {
            "message": "SEO Article Writing System API",
            "status": "running",
            "version": settings.app_version,
            "docs_url": "/docs" if settings.debug else "disabled"
        }
    
    @app.get("/health")
    async def health_check():
        """Detailed health check endpoint."""
        return HealthCheckResponse.get_health_status()
    
    @app.get("/health/ready")
    async def readiness_check():
        """Readiness check for Kubernetes/Docker deployments."""
        # TODO: Check database connectivity
        # TODO: Check Redis connectivity
        # TODO: Check external API availability
        
        return {
            "status": "ready",
            "checks": {
                "database": "connected",  # TODO: Implement real check
                "redis": "connected",     # TODO: Implement real check
                "google_api": "available",  # TODO: Implement real check
                "openai_api": "available"   # TODO: Implement real check
            }
        }
    
    @app.get("/health/live")
    async def liveness_check():
        """Liveness check for Kubernetes/Docker deployments."""
        return {"status": "alive"}
    
    # TODO: 在後續任務中添加路由
    # app.include_router(auth.router, prefix=f"{settings.api_v1_prefix}/auth", tags=["authentication"])
    # app.include_router(research.router, prefix=f"{settings.api_v1_prefix}/research", tags=["research"])
    # app.include_router(content.router, prefix=f"{settings.api_v1_prefix}/content", tags=["content"])
    
    print(f"✅ FastAPI application configured with {len(app.routes)} routes")
    
    return app

# 建立 FastAPI 實例
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )