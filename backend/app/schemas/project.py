"""
Project Schemas.

Pydantic schemas for project-related requests and responses.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# ===== Base Schemas =====

class ProjectBase(BaseModel):
    """Base project schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_market: str = Field(default="tw", max_length=10)
    mode: str = Field(default="existing_site", max_length=50)
    status: str = Field(default="draft", max_length=50)
    domain: Optional[str] = Field(None, max_length=255)


# ===== Request Schemas =====

class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    target_market: Optional[str] = Field(None, max_length=10)
    mode: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=50)
    domain: Optional[str] = Field(None, max_length=255)


# ===== Response Schemas =====

class ProjectResponse(ProjectBase):
    """Schema for project response."""
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class ProjectWithArticles(ProjectResponse):
    """Schema for project with articles list."""
    articles: List["ArticleBrief"] = []


# ===== Brief Schemas (for nested responses) =====

class ArticleBrief(BaseModel):
    """Brief article info for project listing."""
    id: uuid.UUID
    title: str
    status: str
    word_count: int
    created_at: datetime
    
    model_config = {"from_attributes": True}


# Update forward references
ProjectWithArticles.model_rebuild()
