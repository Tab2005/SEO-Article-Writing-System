"""
Brief Schemas.

Pydantic schemas for ArticleBrief request and response models.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ===== Base Schemas =====

class BriefBase(BaseModel):
    """Base schema for ArticleBrief."""
    title_direction: str = Field(..., min_length=1, max_length=500)
    article_role: Optional[str] = Field(None, max_length=50)
    search_intent: Optional[str] = Field(None, max_length=255)
    target_audience: Optional[str] = Field(None, max_length=500)
    primary_question: Optional[str] = None
    next_question: Optional[str] = None
    info_gain_requirement: Optional[str] = None
    restricted_content: Optional[str] = None
    recommended_internal_links: Optional[str] = None
    cta_direction: Optional[str] = None
    status: str = Field(default="draft", max_length=50)


# ===== Request Schemas =====

class BriefCreate(BriefBase):
    """Schema for creating an ArticleBrief."""
    mapped_topic_id: Optional[uuid.UUID] = None
    qualification_id: Optional[uuid.UUID] = None


class BriefUpdate(BaseModel):
    """Schema for updating an ArticleBrief."""
    title_direction: Optional[str] = Field(None, min_length=1, max_length=500)
    article_role: Optional[str] = Field(None, max_length=50)
    search_intent: Optional[str] = Field(None, max_length=255)
    target_audience: Optional[str] = Field(None, max_length=500)
    primary_question: Optional[str] = None
    next_question: Optional[str] = None
    info_gain_requirement: Optional[str] = None
    restricted_content: Optional[str] = None
    recommended_internal_links: Optional[str] = None
    cta_direction: Optional[str] = None
    status: Optional[str] = Field(None, max_length=50)
    mapped_topic_id: Optional[uuid.UUID] = None


# ===== Response Schemas =====

class BriefResponse(BriefBase):
    """Schema for ArticleBrief response."""
    id: uuid.UUID
    project_id: uuid.UUID
    qualification_id: Optional[uuid.UUID] = None
    mapped_topic_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
