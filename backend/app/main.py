from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_v1_router
from app.config import settings

def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title=settings.app_name,
        description="API for AI Content System MVP",
        version="1.0.0",
        debug=settings.debug,
    )
    
    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Adjust as needed in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount API Routers
    application.include_router(api_v1_router, prefix=settings.api_v1_prefix)
    
    from datetime import datetime, timezone
    
    @application.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }
        
    return application


# Create the application instance
app = create_application()

