"""
Content Items API Endpoints.

Handles bulk importing, query, updating, and topic mapping for domain content items.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.content_item import ContentItem
from app.models.topic_node import TopicNode
from app.schemas.content_item import (
    ContentItemImportRequest,
    ContentItemUpdate,
    ContentItemMapTopic,
    ContentItemResponse,
)

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


@router.post("/content-items/import", response_model=List[ContentItemResponse])
async def import_content_items(
    project_id: uuid.UUID,
    import_in: ContentItemImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bulk import content items for existing site analysis."""
    await check_project_owner(db, project_id, current_user.id)
    
    imported_items = []
    for item in import_in.items:
        content_item = ContentItem(
            project_id=project_id,
            title=item.title,
            url=item.url,
            content_type=item.content_type,
            notes=item.notes,
            status="imported"
        )
        db.add(content_item)
        imported_items.append(content_item)
        
    await db.commit()
    for item in imported_items:
        await db.refresh(item)
    return imported_items


@router.get("/content-items", response_model=List[ContentItemResponse])
async def list_content_items(
    project_id: uuid.UUID,
    mapped: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List content items, optionally filtering by mapping status."""
    await check_project_owner(db, project_id, current_user.id)
    
    query = select(ContentItem).where(ContentItem.project_id == project_id)
    if mapped is not None:
        if mapped:
            query = query.where(ContentItem.mapped_topic_id.isnot(None))
          # Handle is_none / is_(None)
        else:
            query = query.where(ContentItem.mapped_topic_id.is_(None))
            
    query = query.order_by(ContentItem.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


@router.patch("/content-items/{item_id}", response_model=ContentItemResponse)
async def update_content_item(
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    item_in: ContentItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Partially update content item details."""
    await check_project_owner(db, project_id, current_user.id)
    
    result = await db.execute(
        select(ContentItem).where(ContentItem.id == item_id, ContentItem.project_id == project_id)
    )
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found.")
        
    update_data = item_in.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(item, key, val)
        
    if "mapped_topic_id" in update_data:
        item.status = "mapped" if update_data["mapped_topic_id"] else "imported"
        
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/content-items/{item_id}/map-topic", response_model=ContentItemResponse)
async def map_content_item_topic(
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    map_in: ContentItemMapTopic,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Map a content item to a specific topic node in the project."""
    await check_project_owner(db, project_id, current_user.id)
    
    result = await db.execute(
        select(ContentItem).where(ContentItem.id == item_id, ContentItem.project_id == project_id)
    )
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found.")
        
    if map_in.mapped_topic_id:
        # Verify node belongs to the same project
        node_res = await db.execute(
            select(TopicNode).where(TopicNode.id == map_in.mapped_topic_id, TopicNode.project_id == project_id)
        )
        node = node_res.scalars().first()
        if not node:
            raise HTTPException(status_code=400, detail="Target topic node not found in this project.")
            
        item.mapped_topic_id = map_in.mapped_topic_id
        item.status = "mapped"
        if node.journey_stage:
            item.journey_stage = node.journey_stage
    else:
        item.mapped_topic_id = None
        item.status = "imported"
        
    await db.commit()
    await db.refresh(item)
    return item
