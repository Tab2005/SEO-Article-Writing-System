"""
Article Schemas.

Pydantic schemas for article-related requests and responses.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

from app.models.article import ArticleStatus


# ===== Base Schemas =====

class ArticleBase(BaseModel):
    """Base article schema."""
    title: str = Field(..., min_length=1, max_length=500)
    target_keyword: str = Field(..., min_length=1, max_length=255)
    secondary_keywords: Optional[List[str]] = None
    meta_description: Optional[str] = Field(None, max_length=500)


# ===== Request Schemas =====

class ArticleCreate(ArticleBase):
    """Schema for creating an article."""
    project_id: uuid.UUID
    content: Optional[str] = None
    outline: Optional[Dict[str, Any]] = None


class ArticleUpdate(BaseModel):
    """Schema for updating an article."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = None
    outline: Optional[Dict[str, Any]] = None
    target_keyword: Optional[str] = None
    secondary_keywords: Optional[List[str]] = None
    meta_description: Optional[str] = Field(None, max_length=500)
    status: Optional[ArticleStatus] = None


class ArticleGenerateRequest(BaseModel):
    """Schema for requesting article generation."""
    project_id: uuid.UUID
    target_keyword: str
    tone: Optional[str] = "professional"
    word_count_target: Optional[int] = Field(default=2000, ge=500, le=10000)
    include_faq: bool = True
    include_table_of_contents: bool = True


# ===== Response Schemas =====

class ArticleResponse(ArticleBase):
    """Schema for article response."""
    id: uuid.UUID
    project_id: uuid.UUID
    slug: Optional[str] = None
    content: Optional[str] = None
    outline: Optional[Dict[str, Any]] = None
    word_count: int
    version: int
    status: ArticleStatus
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ArticleVersionResponse(BaseModel):
    """Schema for article version history."""
    id: uuid.UUID
    version: int
    title: str
    word_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== Outline Schemas =====

class OutlineSection(BaseModel):
    """Schema for article outline section."""
    heading: str
    level: int = Field(..., ge=1, le=4)  # H1-H4
    key_points: List[str] = []
    subsections: List["OutlineSection"] = []


class ArticleOutline(BaseModel):
    """Schema for complete article outline."""
    title: str
    meta_description: str
    sections: List[OutlineSection]
    estimated_word_count: int
    target_keywords: List[str]


# Update forward references
OutlineSection.model_rebuild()
