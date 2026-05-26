"""
Qualification Schemas.

Pydantic schemas for Qualification evaluation requests and results.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ===== Request Schemas =====

class QualificationRequest(BaseModel):
    """Request schema for evaluating a keyword/topic idea."""
    input_term: str = Field(..., min_length=1, max_length=255)


class QualificationUpdate(BaseModel):
    """Request schema for editing evaluation result status or notes."""
    review_status: str = Field(..., description="generated, approved, rejected, edited")
    mapped_topic_id: Optional[uuid.UUID] = None
    suggested_angle: Optional[str] = None
    target_journey_stage: Optional[str] = None


# ===== Response Schemas =====

class QualificationResponse(BaseModel):
    """Response schema for topic evaluation result."""
    id: uuid.UUID
    project_id: uuid.UUID
    input_term: str
    decision: str  # qualified, rewrite_existing, not_qualified
    summary_reason: Optional[str] = None
    mapped_topic_id: Optional[uuid.UUID] = None
    suggested_angle: Optional[str] = None
    target_journey_stage: Optional[str] = None
    
    # 5 Fit dimensions (High, Medium, Low)
    identity_fit: Optional[str] = None
    topic_fit: Optional[str] = None
    audience_fit: Optional[str] = None
    authority_fit: Optional[str] = None
    business_fit: Optional[str] = None
    
    # 2 Risk dimensions (High, Medium, Low, None)
    overlap_risk: Optional[str] = None
    boundary_risk: Optional[str] = None
    
    risks: Optional[List[str]] = None
    alternative_topics: Optional[List[str]] = None
    recommended_next_step: Optional[str] = None
    
    review_status: str
    created_at: datetime

    model_config = {"from_attributes": True}
