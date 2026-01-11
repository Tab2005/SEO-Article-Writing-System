"""
Content API Endpoints.

Handles AI-powered content generation.
"""

from typing import Optional, List
import uuid

from fastapi import APIRouter, status, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.research_job import ResearchArtifact
from app.schemas.article import (
    ArticleOutline,
    ArticleGenerateRequest,
    ArticleResponse,
)
from app.services import llm_service, analysis_service, google_search_service, crawler_service

router = APIRouter()


class OutlineRequest(BaseModel):
    """Request schema for outline generation."""
    topic: str = Field(..., min_length=1, max_length=500)
    target_keyword: str = Field(..., min_length=1, max_length=255)
    secondary_keywords: List[str] = Field(default=[], max_length=10)
    word_count_target: int = Field(default=2000, ge=500, le=10000)
    tone: str = Field(default="professional")
    use_competitor_analysis: bool = Field(default=True)
    market: str = Field(default="tw")
    research_job_id: Optional[uuid.UUID] = None


class ContentRequest(BaseModel):
    """Request schema for full content generation."""
    topic: str = Field(..., min_length=1, max_length=500)
    target_keyword: str = Field(..., min_length=1, max_length=255)
    secondary_keywords: List[str] = Field(default=[], max_length=10)
    word_count_target: int = Field(default=2000, ge=500, le=10000)
    tone: str = Field(default="professional")
    market: str = Field(default="tw")
    research_job_id: Optional[uuid.UUID] = None


class ContentOptimizeRequest(BaseModel):
    """Request schema for content optimization."""
    content: str = Field(..., min_length=100)
    target_keywords: List[str] = Field(..., min_length=1)


@router.post("/outline", status_code=status.HTTP_201_CREATED, response_model=ArticleOutline)
async def generate_outline(request: OutlineRequest, db: AsyncSession = Depends(get_db)):
    """
    Generate article outline.
    
    Uses AI to create SEO-optimized article structure.
    Optionally analyzes competitors for better context.
    """
    competitor_h2s = None
    
    if request.research_job_id:
        try:
            result = await db.execute(
                select(ResearchArtifact)
                .where(
                    ResearchArtifact.job_id == request.research_job_id,
                    ResearchArtifact.type == "analysis_report",
                )
                .order_by(ResearchArtifact.created_at.desc())
                .limit(1)
            )
            artifact = result.scalar_one_or_none()
            if artifact:
                competitor_h2s = (artifact.payload or {}).get("common_h2_tags")
        except Exception:
            competitor_h2s = None

    if request.use_competitor_analysis and not competitor_h2s:
        try:
            # Get SERP results
            serp = await google_search_service.search(
                keyword=request.target_keyword,
                market=request.market,
                num_results=5,
            )
            
            # Crawl competitors
            urls = [r.url for r in serp.results]
            competitors = await crawler_service.crawl_pages(urls)
            
            # Extract common H2s
            competitor_h2s = analysis_service.extract_common_headings(
                competitors, "h2", 10
            )
        except Exception:
            # Continue without competitor analysis if it fails
            pass
    
    outline = await llm_service.generate_outline(
        topic=request.topic,
        target_keyword=request.target_keyword,
        secondary_keywords=request.secondary_keywords,
        competitor_h2s=competitor_h2s,
        word_count_target=request.word_count_target,
        tone=request.tone,
    )
    
    return outline


@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_content(request: ContentRequest, db: AsyncSession = Depends(get_db)):
    """
    Generate full article content.
    
    Creates complete article based on topic and keywords.
    Includes competitor analysis for SEO optimization.
    """
    # Step 1: Get competitor insights
    competitor_h2s = None
    if request.research_job_id:
        try:
            result = await db.execute(
                select(ResearchArtifact)
                .where(
                    ResearchArtifact.job_id == request.research_job_id,
                    ResearchArtifact.type == "analysis_report",
                )
                .order_by(ResearchArtifact.created_at.desc())
                .limit(1)
            )
            artifact = result.scalar_one_or_none()
            if artifact:
                competitor_h2s = (artifact.payload or {}).get("common_h2_tags")
        except Exception:
            competitor_h2s = None

    if not competitor_h2s:
        try:
            serp = await google_search_service.search(
                keyword=request.target_keyword,
                market=request.market,
                num_results=5,
            )
            urls = [r.url for r in serp.results]
            competitors = await crawler_service.crawl_pages(urls)
            competitor_h2s = analysis_service.extract_common_headings(competitors, "h2", 10)
        except Exception:
            pass
    
    # Step 2: Generate outline
    outline = await llm_service.generate_outline(
        topic=request.topic,
        target_keyword=request.target_keyword,
        secondary_keywords=request.secondary_keywords,
        competitor_h2s=competitor_h2s,
        word_count_target=request.word_count_target,
        tone=request.tone,
    )
    
    # Step 3: Generate full content
    content = await llm_service.generate_full_article(
        outline=outline,
        target_keyword=request.target_keyword,
        secondary_keywords=request.secondary_keywords,
    )
    
    return {
        "outline": outline,
        "content": content,
        "word_count": len(content),
        "target_keyword": request.target_keyword,
        "secondary_keywords": request.secondary_keywords,
    }


@router.post("/optimize")
async def optimize_content(request: ContentOptimizeRequest):
    """
    Optimize existing content for SEO.
    
    Improves keyword density and readability.
    """
    optimized = await llm_service.optimize_content(
        content=request.content,
        target_keywords=request.target_keywords,
    )
    
    return {
        "original_length": len(request.content),
        "optimized_length": len(optimized),
        "content": optimized,
    }


@router.patch("/{article_id}")
async def update_article(article_id: str):
    """
    Update article content.
    
    Saves edited content and creates new version.
    """
    # TODO: Implement with database in future task
    return {"message": f"Update article {article_id} - To be implemented with database"}


@router.get("/{article_id}/versions")
async def get_article_versions(article_id: str):
    """
    Get article version history.
    
    Returns list of previous versions for comparison.
    """
    # TODO: Implement with database
    return {"message": f"Article versions for {article_id} - To be implemented"}
