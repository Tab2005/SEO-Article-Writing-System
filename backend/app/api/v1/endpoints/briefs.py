"""
Brief API Endpoints.

Handles planning layer article briefs API routes.
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.schemas.brief import (
    BriefCreate,
    BriefUpdate,
    BriefResponse,
)
from app.services.brief_service import brief_service
from app.core.exceptions import NotFoundException, BadRequestException

router = APIRouter()


async def check_project_owner(db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID) -> Project:
    """Helper to verify project exists and belongs to current user."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == user_id)
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or access denied.")
    return project


@router.get("/briefs", response_model=List[BriefResponse])
async def list_briefs(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all article briefs in a project."""
    await check_project_owner(db, project_id, current_user.id)
    return await brief_service.list_by_project(db, project_id)


@router.post("/briefs", response_model=BriefResponse, status_code=status.HTTP_201_CREATED)
async def create_brief(
    project_id: uuid.UUID,
    brief_in: BriefCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create an article brief manually."""
    await check_project_owner(db, project_id, current_user.id)
    try:
        return await brief_service.create_brief(
            db, project_id, brief_in.model_dump(exclude_unset=True)
        )
    except (NotFoundException, BadRequestException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/briefs/from-qualification/{qualification_id}", response_model=BriefResponse, status_code=status.HTTP_201_CREATED)
async def create_brief_from_qualification(
    project_id: uuid.UUID,
    qualification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a structured article brief from a Qualified topic idea."""
    await check_project_owner(db, project_id, current_user.id)
    try:
        return await brief_service.create_from_qualification(db, project_id, qualification_id)
    except (NotFoundException, BadRequestException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/briefs/{brief_id}", response_model=BriefResponse)
async def get_brief(
    project_id: uuid.UUID,
    brief_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed single article brief."""
    await check_project_owner(db, project_id, current_user.id)
    brief = await brief_service.get_brief(db, brief_id)
    if not brief or brief.project_id != project_id:
        raise HTTPException(status_code=404, detail="Article brief not found.")
    return brief


@router.patch("/briefs/{brief_id}", response_model=BriefResponse)
async def update_brief(
    project_id: uuid.UUID,
    brief_id: uuid.UUID,
    brief_in: BriefUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update article brief details."""
    await check_project_owner(db, project_id, current_user.id)
    brief = await brief_service.get_brief(db, brief_id)
    if not brief or brief.project_id != project_id:
        raise HTTPException(status_code=404, detail="Article brief not found.")
    try:
        return await brief_service.update_brief(
            db, brief_id, brief_in.model_dump(exclude_unset=True)
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/briefs/{brief_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brief(
    project_id: uuid.UUID,
    brief_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an article brief."""
    await check_project_owner(db, project_id, current_user.id)
    brief = await brief_service.get_brief(db, brief_id)
    if not brief or brief.project_id != project_id:
        raise HTTPException(status_code=404, detail="Article brief not found.")
    try:
        await brief_service.delete_brief(db, brief_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
