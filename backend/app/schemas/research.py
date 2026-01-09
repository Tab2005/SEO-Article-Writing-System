"""
Research Schemas.

Pydantic schemas for keyword research and competitor analysis.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, HttpUrl


# ===== Request Schemas =====

class KeywordResearchRequest(BaseModel):
    """Schema for keyword research request."""
    keyword: str = Field(..., min_length=1, max_length=200)
    market: str = Field(default="tw", max_length=10)
    depth: int = Field(default=10, ge=1, le=50)  # Number of results


class CompetitorCrawlRequest(BaseModel):
    """Schema for competitor crawling request."""
    url: HttpUrl
    extract_headings: bool = True
    extract_meta: bool = True
    calculate_word_count: bool = True


# ===== SERP Result Schemas =====

class SerpResult(BaseModel):
    """Schema for single SERP result."""
    rank: int
    title: str
    url: str
    snippet: str
    scraped_at: Optional[datetime] = None


class SerpResponse(BaseModel):
    """Schema for SERP search response."""
    keyword: str
    market: str
    total_results: int
    results: List[SerpResult]
    cached: bool = False
    fetched_at: datetime


# ===== Competitor Analysis Schemas =====

class HeadingStructure(BaseModel):
    """Schema for extracted heading structure."""
    h1: List[str] = []
    h2: List[str] = []
    h3: List[str] = []


class CompetitorData(BaseModel):
    """Schema for competitor page analysis."""
    rank: int
    url: str
    title: str
    word_count: int
    headings: HeadingStructure
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    scraped_at: datetime


class AnalysisReport(BaseModel):
    """Schema for complete competitor analysis report."""
    keyword: str
    market: str
    avg_word_count: int
    min_word_count: int
    max_word_count: int
    common_h2_tags: List[str]
    common_h3_tags: List[str]
    keyword_frequency: Dict[str, int]
    competitor_count: int
    competitors: List[CompetitorData]
    generated_at: datetime


# ===== Task Status Schemas =====

class ResearchTaskStatus(BaseModel):
    """Schema for research task status."""
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: int = Field(..., ge=0, le=100)
    message: Optional[str] = None
    result: Optional[AnalysisReport] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class ResearchTaskCreate(BaseModel):
    """Schema for created research task response."""
    task_id: str
    keyword: str
    market: str
    status: str = "pending"
    message: str = "Research task created"
