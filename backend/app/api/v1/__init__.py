"""
V1 API Router.

Aggregates all v1 API endpoints.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, research, content, projects, seo, websocket

api_v1_router = APIRouter()

# Include routers
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(research.router, prefix="/research", tags=["Research"])
api_v1_router.include_router(content.router, prefix="/content", tags=["Content"])
api_v1_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_v1_router.include_router(seo.router, prefix="/seo", tags=["SEO"])
api_v1_router.include_router(websocket.router, tags=["WebSocket"])
