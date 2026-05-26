"""
Site Profile Schemas.

Pydantic schemas for Site Profile requests and responses.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ===== Base Schemas =====

class SiteProfileBase(BaseModel):
    """Base site profile schema."""
    site_name: str = Field(..., min_length=1, max_length=255)
    business_type: Optional[str] = Field(None, max_length=255)
    site_description: Optional[str] = None
    target_audiences: Optional[List[str]] = None
    products_or_services: Optional[List[str]] = None
    core_topics: Optional[List[str]] = None
    allowed_angles: Optional[List[str]] = None
    restricted_angles: Optional[List[str]] = None
    brand_voice: Optional[str] = None
    proof_assets: Optional[List[str]] = None
    primary_goals: Optional[List[str]] = None
    geo_focus: Optional[List[str]] = None
    industry_constraints: Optional[List[str]] = None
    editorial_notes: Optional[str] = None
    status: str = Field(default="draft", max_length=50)


# ===== Request Schemas =====

class SiteProfileCreate(SiteProfileBase):
    """Schema for creating a site profile."""
    pass


class SiteProfileUpdate(BaseModel):
    """Schema for updating a site profile."""
    site_name: Optional[str] = Field(None, min_length=1, max_length=255)
    business_type: Optional[str] = Field(None, max_length=255)
    site_description: Optional[str] = None
    target_audiences: Optional[List[str]] = None
    products_or_services: Optional[List[str]] = None
    core_topics: Optional[List[str]] = None
    allowed_angles: Optional[List[str]] = None
    restricted_angles: Optional[List[str]] = None
    brand_voice: Optional[str] = None
    proof_assets: Optional[List[str]] = None
    primary_goals: Optional[List[str]] = None
    geo_focus: Optional[List[str]] = None
    industry_constraints: Optional[List[str]] = None
    editorial_notes: Optional[str] = None
    status: Optional[str] = Field(None, max_length=50)


# ===== Response Schemas =====

class SiteProfileResponse(SiteProfileBase):
    """Schema for site profile response."""
    id: uuid.UUID
    project_id: uuid.UUID
    summary_snapshot: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
