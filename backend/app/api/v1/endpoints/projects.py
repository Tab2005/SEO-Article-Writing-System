"""
Projects API Endpoints.

Handles project management operations with mode, status, and planning validation.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.site_profile import SiteProfile
from app.models.topic_node import TopicNode
from app.models.article_brief import ArticleBrief
from app.models.qualification_result import QualificationResult
from app.models.article import Article, ArticleStatus
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.schemas.content_queue import ContentQueueItemResponse
from app.services.seed_service import seed_service
from app.services.site_profile_service import site_profile_service


router = APIRouter()


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all projects for the current user."""
    result = await db.execute(
        select(Project)
        .where(Project.owner_id == current_user.id)
        .order_by(Project.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new project."""
    project = Project(
        owner_id=current_user.id,
        name=project_in.name,
        description=project_in.description,
        target_market=project_in.target_market,
        mode=project_in.mode,
        status=project_in.status,
        domain=project_in.domain,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get project details by ID."""
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    project_in: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update project details."""
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
        
    update_data = project_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
        
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a project."""
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
        
    await db.delete(project)
    await db.commit()
    return None


@router.post("/{project_id}/activate", response_model=ProjectResponse)
async def activate_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Activate project after planning phase is completed.
    
    Checks:
    1. Site Profile must exist and status == "ready"
    2. Topic Map must have at least one active (non-archived) Topic Node
    """
    # Load project with relationships
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id, Project.owner_id == current_user.id)
        .options(
            selectinload(Project.site_profile),
            selectinload(Project.topic_nodes)
        )
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    # 1. Site Profile status check
    if not project.site_profile:
        raise HTTPException(
            status_code=400,
            detail="Cannot activate project: Site Profile has not been configured."
        )
    readiness_issues, status_changed = site_profile_service.sync_status(project.site_profile)
    if status_changed:
        await db.commit()
        await db.refresh(project.site_profile)
    if readiness_issues:
        missing_fields = ", ".join(readiness_issues)
        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot activate project: Site Profile is incomplete. "
                f"Missing required fields: {missing_fields}."
            ),
        )

    # 2. Topic Map check (must have at least 1 active topic node)
    active_nodes = [node for node in project.topic_nodes if node.status == "active"]
    if not active_nodes:
        raise HTTPException(
            status_code=400,
            detail="Cannot activate project: Topic Map must have at least one active Topic Node."
        )

    project.status = "active"
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}/content-queue", response_model=List[ContentQueueItemResponse])
async def get_project_content_queue(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the content queue for a project, aggregating topics, briefs, and drafts.
    """
    # Verify project exists and belongs to the user
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    # 1. Query all ArticleBriefs and their related entities
    briefs_result = await db.execute(
        select(ArticleBrief)
        .where(ArticleBrief.project_id == project_id)
        .options(
            selectinload(ArticleBrief.mapped_topic),
            selectinload(ArticleBrief.qualification),
            selectinload(ArticleBrief.articles)
        )
    )
    briefs = briefs_result.scalars().all()

    # 2. Query all decision == "qualified" and unlinked QualificationResults
    associated_qualification_ids = {b.qualification_id for b in briefs if b.qualification_id is not None}
    
    qualifications_query = select(QualificationResult).where(
        QualificationResult.project_id == project_id,
        QualificationResult.decision == "qualified"
    )
    if associated_qualification_ids:
        qualifications_query = qualifications_query.where(
            QualificationResult.id.not_in(list(associated_qualification_ids))
        )
    
    qualifications_result = await db.execute(
        qualifications_query.options(selectinload(QualificationResult.mapped_topic))
    )
    qualifications = qualifications_result.scalars().all()

    queue_items = []

    # Process briefs
    for brief in briefs:
        # Find the main article (parent_version_id is None)
        main_article = None
        for art in brief.articles:
            if art.parent_version_id is None:
                main_article = art
                break

        # Determine status
        status = "brief_draft"
        if brief.status == "approved":
            status = "brief_approved"
        
        draft_id = None
        if main_article:
            draft_id = main_article.id
            if main_article.status == ArticleStatus.PUBLISHED:
                status = "completed"
            else:
                if main_article.qa_status == "passed":
                    status = "qa_passed"
                elif main_article.qa_status == "failed":
                    status = "qa_failed"
                else:
                    status = "draft_writing"

        # Determine keyword
        keyword = brief.title_direction
        if brief.qualification:
            keyword = brief.qualification.input_term

        # Determine journey stage
        journey_stage = None
        if brief.mapped_topic:
            journey_stage = brief.mapped_topic.journey_stage
        elif brief.qualification:
            journey_stage = brief.qualification.target_journey_stage

        # Update timestamp should be the latest among brief and main article
        updated_at = brief.updated_at
        if main_article and main_article.updated_at > updated_at:
            updated_at = main_article.updated_at

        queue_items.append(
            ContentQueueItemResponse(
                id=brief.id,
                keyword=keyword,
                journey_stage=journey_stage,
                topic_id=brief.mapped_topic_id,
                topic_name=brief.mapped_topic.name if brief.mapped_topic else None,
                status=status,
                created_at=brief.created_at,
                updated_at=updated_at,
                qualification_id=brief.qualification_id,
                brief_id=brief.id,
                draft_id=draft_id
            )
        )

    # Process qualified, unlinked topics
    for qual in qualifications:
        queue_items.append(
            ContentQueueItemResponse(
                id=qual.id,
                keyword=qual.input_term,
                journey_stage=qual.target_journey_stage,
                topic_id=qual.mapped_topic_id,
                topic_name=qual.mapped_topic.name if qual.mapped_topic else None,
                status="qualified",
                created_at=qual.created_at,
                updated_at=qual.created_at,
                qualification_id=qual.id,
                brief_id=None,
                draft_id=None
            )
        )

    # Sort queue items by updated_at desc
    queue_items.sort(key=lambda x: x.updated_at, reverse=True)
    return queue_items


@router.post("/seed-demo")
async def seed_demo(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Seed demo projects for the current user.
    """
    return await seed_service.seed_demo_data(db, current_user.id)
