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


# ===== Topic Theme Schemas =====

class TopicTheme(BaseModel):
    """Schema for semantic topic theme extracted from competitor headings."""
    theme_name: str  # e.g. "步驟流程", "工具推薦"
    coverage_count: int  # How many competitors cover this theme
    total_competitors: int  # Total competitors analyzed
    example_headings: List[str] = []  # Sample headings in this theme


# ===== TF-IDF Keyword Schemas =====

class KeywordItem(BaseModel):
    """Schema for a single keyword with score."""
    term: str
    score: float


class KeywordCount(BaseModel):
    """Schema for keyword with count."""
    term: str
    count: int


class KeywordCategories(BaseModel):
    """Schema for categorized keywords."""
    high_frequency: List[KeywordItem] = []  # 高頻核心詞
    semantic_related: List[KeywordItem] = []  # 語意相關詞
    long_tail: List[KeywordItem] = []  # 長尾關鍵詞


class TFIDFAnalysis(BaseModel):
    """Schema for TF-IDF keyword analysis results."""
    suggested_keywords: List[KeywordItem] = []  # 建議使用的關鍵詞
    keyword_categories: KeywordCategories = KeywordCategories()
    competitor_common_terms: List[KeywordCount] = []  # 競品共同出現的詞


class AnalysisReport(BaseModel):
    """Schema for complete competitor analysis report."""
    keyword: str
    market: str
    avg_word_count: int
    min_word_count: int
    max_word_count: int
    common_h2_tags: List[str]
    common_h3_tags: List[str]
    topic_themes: List[TopicTheme] = []  # Semantic topic themes
    keyword_frequency: Dict[str, int]
    tfidf_analysis: Optional[TFIDFAnalysis] = None  # TF-IDF 關鍵詞分析
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
