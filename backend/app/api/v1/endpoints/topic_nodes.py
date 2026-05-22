"""
Topic Nodes API Endpoints.

Handles Topic Map tree nodes hierarchy management, move, archive, and gap analysis.
"""

import uuid
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.topic_node import TopicNode
from app.schemas.topic_node import (
    TopicNodeCreate,
    TopicNodeUpdate,
    TopicNodeMove,
    TopicNodeResponse,
)
from app.services.topic_map_service import topic_map_service
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


@router.get("/topic-nodes", response_model=List[Any])
async def list_topic_nodes(
    project_id: uuid.UUID,
    tree: bool = Query(False, description="Return hierarchical tree structures if True"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List topic nodes. Returns tree structure if tree=True, else flat list."""
    await check_project_owner(db, project_id, current_user.id)
    if tree:
        return await topic_map_service.get_tree(db, project_id)
    else:
        return await topic_map_service.list_by_project(db, project_id)


@router.post("/topic-nodes", response_model=TopicNodeResponse, status_code=status.HTTP_201_CREATED)
async def create_topic_node(
    project_id: uuid.UUID,
    node_in: TopicNodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new topic node in the project."""
    await check_project_owner(db, project_id, current_user.id)
    try:
        node = await topic_map_service.create_node(db, project_id, node_in.model_dump())
        return node
    except (NotFoundException, BadRequestException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/topic-nodes/{node_id}", response_model=TopicNodeResponse)
async def update_topic_node(
    project_id: uuid.UUID,
    node_id: uuid.UUID,
    node_in: TopicNodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update topic node details."""
    await check_project_owner(db, project_id, current_user.id)
    # Check node belongs to project
    node = await topic_map_service.get_node(db, node_id)
    if not node or node.project_id != project_id:
        raise HTTPException(status_code=404, detail="Topic node not found in this project.")
        
    try:
        updated_node = await topic_map_service.update_node(db, node_id, node_in.model_dump(exclude_unset=True))
        return updated_node
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/topic-nodes/{node_id}/move", response_model=TopicNodeResponse)
async def move_topic_node(
    project_id: uuid.UUID,
    node_id: uuid.UUID,
    move_in: TopicNodeMove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Move a topic node to a different parent (with loop prevention)."""
    await check_project_owner(db, project_id, current_user.id)
    node = await topic_map_service.get_node(db, node_id)
    if not node or node.project_id != project_id:
        raise HTTPException(status_code=404, detail="Topic node not found in this project.")
        
    try:
        moved_node = await topic_map_service.move_node(db, node_id, move_in.parent_id)
        return moved_node
    except (NotFoundException, BadRequestException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/topic-nodes/{node_id}/archive", response_model=TopicNodeResponse)
async def archive_topic_node(
    project_id: uuid.UUID,
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Archive a topic node (changes its status to archived)."""
    await check_project_owner(db, project_id, current_user.id)
    node = await topic_map_service.get_node(db, node_id)
    if not node or node.project_id != project_id:
        raise HTTPException(status_code=404, detail="Topic node not found in this project.")
        
    node.status = "archived"
    await db.commit()
    await db.refresh(node)
    return node


@router.get("/topic-map/gaps", response_model=List[Dict[str, Any]])
async def list_topic_map_gaps(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze the project's topic map for empty pillar nodes or unmapped content library gaps."""
    await check_project_owner(db, project_id, current_user.id)
    try:
        gaps = await topic_map_service.list_gaps(db, project_id)
        return gaps
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
