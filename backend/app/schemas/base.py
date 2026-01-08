"""
Base Pydantic schemas for common response patterns

This module provides base schemas that are used across multiple API endpoints
for consistent response formatting and validation.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class BaseSchema(BaseModel):
    """Base schema for all Pydantic models with common configuration."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid',
        from_attributes=True
    )

class BaseResponse(BaseModel):
    """Base response model for all API responses."""
    
    success: bool = Field(default=True, description="Indicates if the request was successful")
    message: Optional[str] = Field(default=None, description="Human-readable message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

class ErrorDetail(BaseModel):
    """Error detail structure."""
    
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional error details")

class ErrorResponse(BaseResponse):
    """Error response model."""
    
    success: bool = Field(default=False)
    error: ErrorDetail = Field(..., description="Error information")

class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=100, ge=1, le=100, description="Maximum number of records to return")

class PaginatedResponse(BaseResponse):
    """Paginated response model."""
    
    total: int = Field(..., description="Total number of records")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")
    has_more: bool = Field(..., description="Whether there are more records available")

class TaskStatus(BaseModel):
    """Background task status model."""
    
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Task status (pending, running, completed, failed)")
    progress: int = Field(default=0, ge=0, le=100, description="Task progress percentage")
    message: Optional[str] = Field(default=None, description="Current task message")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    error: Optional[str] = Field(default=None, description="Error message if task failed")

class HealthCheck(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Overall system status")
    timestamp: float = Field(..., description="Check timestamp")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    services: Dict[str, Any] = Field(default_factory=dict, description="Service status details")

class APIKeyInfo(BaseModel):
    """API key information (without exposing the actual key)."""
    
    name: str = Field(..., description="API key name/service")
    configured: bool = Field(..., description="Whether the API key is configured")
    valid: Optional[bool] = Field(default=None, description="Whether the API key is valid (if tested)")
    last_tested: Optional[datetime] = Field(default=None, description="Last time the API key was tested")
    usage_limit: Optional[int] = Field(default=None, description="Daily/monthly usage limit")
    usage_current: Optional[int] = Field(default=None, description="Current usage count")

class ValidationError(BaseModel):
    """Validation error detail."""
    
    field: str = Field(..., description="Field name that failed validation")
    message: str = Field(..., description="Validation error message")
    value: Any = Field(default=None, description="Value that failed validation")