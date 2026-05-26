"""
Content Queue Schemas.

Pydantic schemas for the Operational Layer Content Queue endpoints.
"""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ContentQueueItemResponse(BaseModel):
    """Schema representing an item in the Content Queue."""
    id: uuid.UUID = Field(..., description="The unique identifier for the queue item (usually brief_id, or qualification_id)")
    keyword: str = Field(..., description="The target keyword or topic")
    journey_stage: Optional[str] = Field(None, description="Journey stage (awareness, consideration, decision)")
    topic_id: Optional[uuid.UUID] = Field(None, description="Associated topic node ID")
    topic_name: Optional[str] = Field(None, description="Associated topic node name")
    
    # Stage progress status: qualified, brief_draft, brief_approved, draft_writing, qa_failed, qa_passed, completed
    status: str = Field(..., description="Current content queue stage status")
    
    created_at: datetime
    updated_at: datetime
    
    # Associated resource IDs
    qualification_id: Optional[uuid.UUID] = None
    brief_id: Optional[uuid.UUID] = None
    draft_id: Optional[uuid.UUID] = None
    
    model_config = {"from_attributes": True}
