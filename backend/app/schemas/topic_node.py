"""
Topic Node Schemas.

Pydantic schemas for Topic Node requests and responses.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ===== Base Schemas =====

class TopicNodeBase(BaseModel):
    """Base topic node schema."""
    name: str = Field(..., min_length=1, max_length=255)
    topic_role: str = Field(..., description="pillar, supporting, bridge, comparison, decision, faq")
    description: Optional[str] = None
    journey_stage: Optional[str] = Field(None, description="awareness, consideration, decision")
    priority: str = Field(default="medium", description="high, medium, low")
    supports: Optional[List[str]] = None
    supported_by: Optional[List[str]] = None
    status: str = Field(default="draft", description="draft, active, archived")
    sort_order: int = 0


# ===== Request Schemas =====

class TopicNodeCreate(TopicNodeBase):
    """Schema for creating a topic node."""
    parent_id: Optional[uuid.UUID] = None


class TopicNodeUpdate(BaseModel):
    """Schema for updating a topic node."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    topic_role: Optional[str] = None
    description: Optional[str] = None
    journey_stage: Optional[str] = None
    priority: Optional[str] = None
    supports: Optional[List[str]] = None
    supported_by: Optional[List[str]] = None
    status: Optional[str] = None
    sort_order: Optional[int] = None


class TopicNodeMove(BaseModel):
    """Schema for moving a topic node to another parent."""
    parent_id: Optional[uuid.UUID] = None


# ===== Response Schemas =====

class TopicNodeResponse(TopicNodeBase):
    """Schema for topic node response."""
    id: uuid.UUID
    project_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TopicNodeTreeResponse(TopicNodeResponse):
    """Schema for topic node tree node with children."""
    children: List["TopicNodeTreeResponse"] = []

# Rebuild model for self-reference
TopicNodeTreeResponse.model_rebuild()
