"""
API v1 Router.

Aggregates all v1 API endpoints.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, research, content, projects

router = APIRouter()

# Include endpoint routers
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(research.router, prefix="/research", tags=["Research"])
router.include_router(content.router, prefix="/content", tags=["Content"])
router.include_router(projects.router, prefix="/projects", tags=["Projects"])
