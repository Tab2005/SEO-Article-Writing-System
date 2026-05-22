"""
Qualification API Endpoints.

Handles evaluating new topics, listing history, and updating review status.
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
from app.schemas.qualification import (
    QualificationRequest,
    QualificationUpdate,
    QualificationResponse,
)
from app.services.qualification_service import qualification_service
from app.core.exceptions import NotFoundException, BadRequestException

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


@router.post("/qualification-results", response_model=QualificationResponse, status_code=status.HTTP_201_CREATED)
async def evaluate_topic(
    project_id: uuid.UUID,
    req_in: QualificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Evaluate a keyword/topic idea using rules and LLM suitability analysis."""
    await check_project_owner(db, project_id, current_user.id)
    try:
        result = await qualification_service.evaluate_topic(db, project_id, req_in.input_term)
        return result
    except (NotFoundException, BadRequestException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/qualification-results", response_model=List[QualificationResponse])
async def list_qualification_results(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all topic qualification histories in a project."""
    await check_project_owner(db, project_id, current_user.id)
    return await qualification_service.list_by_project(db, project_id)


@router.get("/qualification-results/{result_id}", response_model=QualificationResponse)
async def get_qualification_result(
    project_id: uuid.UUID,
    result_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed single qualification result."""
    await check_project_owner(db, project_id, current_user.id)
    result = await qualification_service.get_result(db, result_id)
    if not result or result.project_id != project_id:
        raise HTTPException(status_code=404, detail="Qualification result not found in this project.")
    return result


@router.patch("/qualification-results/{result_id}", response_model=QualificationResponse)
async def update_qualification_result(
    project_id: uuid.UUID,
    result_id: uuid.UUID,
    update_in: QualificationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update review status, suggested angle, or map to a topic node."""
    await check_project_owner(db, project_id, current_user.id)
    result = await qualification_service.get_result(db, result_id)
    if not result or result.project_id != project_id:
        raise HTTPException(status_code=404, detail="Qualification result not found in this project.")
        
    try:
        updated = await qualification_service.update_result(
            db, result_id, update_in.model_dump(exclude_unset=True)
        )
        return updated
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
