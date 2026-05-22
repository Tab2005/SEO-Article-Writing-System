"""
Site Profiles API Endpoints.

Handles Site Profile CRUD operations and AI snapshot generation.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.schemas.site_profile import SiteProfileCreate, SiteProfileUpdate, SiteProfileResponse
from app.services.site_profile_service import site_profile_service

router = APIRouter()


async def check_project_owner(db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID) -> Project:
    """Helper to verify project exists and belongs to current user."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == user_id)
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


@router.get("", response_model=SiteProfileResponse)
async def get_site_profile(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get site profile for a project."""
    await check_project_owner(db, project_id, current_user.id)
    profile = await site_profile_service.get_by_project(db, project_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Site Profile not found.")
    return profile


@router.put("", response_model=SiteProfileResponse)
async def create_or_overwrite_site_profile(
    project_id: uuid.UUID,
    profile_in: SiteProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create or overwrite a site profile."""
    await check_project_owner(db, project_id, current_user.id)
    profile_data = profile_in.model_dump()
    profile = await site_profile_service.create_or_update(db, project_id, profile_data)
    return profile


@router.patch("", response_model=SiteProfileResponse)
async def update_site_profile(
    project_id: uuid.UUID,
    profile_in: SiteProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Partially update site profile."""
    await check_project_owner(db, project_id, current_user.id)
    profile_data = profile_in.model_dump(exclude_unset=True)
    profile = await site_profile_service.create_or_update(db, project_id, profile_data)
    return profile


@router.post("/summarize", response_model=SiteProfileResponse)
async def summarize_site_profile(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate brand snapshot summary using LLM."""
    await check_project_owner(db, project_id, current_user.id)
    try:
        profile = await site_profile_service.generate_snapshot(db, project_id)
        return profile
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
