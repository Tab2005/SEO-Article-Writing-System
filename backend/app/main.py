"""
FastAPI Application Entry Point.

SEO Article Writing System - A comprehensive platform for 
keyword research, competitor analysis, and AI-powered content generation.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1 import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    print(f"🚀 Starting {settings.app_name}...")
    yield
    # Shutdown
    print(f"👋 Shutting down {settings.app_name}...")


def create_application() -> FastAPI:
    """
    Application factory.
    
    Creates and configures the FastAPI application instance.
    """
    app = FastAPI(
        title=settings.app_name,
        description="SEO Article Writing System API - Keyword research, competitor analysis, and AI content generation.",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
    
    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "app": settings.app_name}
    
    return app


# Create the application instance
app = create_application()
