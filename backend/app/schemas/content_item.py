"""
Content Item Schemas.

Pydantic schemas for Content Item requests and responses.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ===== Base Schemas =====

class ContentItemBase(BaseModel):
    """Base content item schema."""
    title: str = Field(..., min_length=1, max_length=512)
    url: Optional[str] = Field(None, max_length=1024)
    content_type: str = Field(default="article", max_length=50)
    journey_stage: Optional[str] = Field(None, max_length=50)
    status: str = Field(default="imported", max_length=50)
    notes: Optional[str] = None


# ===== Request Schemas =====

class ContentItemSingleImport(BaseModel):
    """Single item model for import request."""
    title: str = Field(..., min_length=1, max_length=512)
    url: Optional[str] = Field(None, max_length=1024)
    content_type: str = Field(default="article", max_length=50)
    notes: Optional[str] = None


class ContentItemImportRequest(BaseModel):
    """Request schema for importing multiple content items."""
    items: List[ContentItemSingleImport]


class ContentItemUpdate(BaseModel):
    """Schema for updating content item fields."""
    title: Optional[str] = Field(None, min_length=1, max_length=512)
    url: Optional[str] = Field(None, max_length=1024)
    content_type: Optional[str] = None
    mapped_topic_id: Optional[uuid.UUID] = None
    journey_stage: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ContentItemMapTopic(BaseModel):
    """Schema for mapping content item to a topic node."""
    mapped_topic_id: Optional[uuid.UUID] = None


# ===== Response Schemas =====

class ContentItemResponse(ContentItemBase):
    """Schema for content item response."""
    id: uuid.UUID
    project_id: uuid.UUID
    mapped_topic_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
