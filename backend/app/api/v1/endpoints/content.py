"""
Content API Endpoints.

Handles AI-powered content generation.
"""

from typing import Optional, List, Dict, Any
import uuid

from fastapi import APIRouter, status, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.research_job import ResearchArtifact
from app.models.article import Article, ArticleStatus
from app.schemas.article import (
    ArticleOutline,
    ArticleGenerateRequest,
    ArticleResponse,
    OutlineSection,
)
from app.services import llm_service, analysis_service, google_search_service, crawler_service
from app.services.strategy_service import strategy_service, StrategyPack
from app.services.article_draft_service import article_draft_service
from app.services.streaming_service import streaming_service

router = APIRouter()


class StrategyRequest(BaseModel):
    """Request schema for strategy pack generation."""
    keyword: str = Field(..., min_length=1, max_length=255)
    market: str = Field(default="tw")
    job_id: Optional[uuid.UUID] = None
    intent: Optional[str] = None
    tone: Optional[str] = None
    regenerate_titles: bool = Field(default=False)


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


@router.post("/strategy", status_code=status.HTTP_200_OK, response_model=StrategyPack)
async def generate_strategy(request: StrategyRequest, db: AsyncSession = Depends(get_db)):
    """
    Generate content strategy pack.
    
    Returns comprehensive strategy recommendations including:
    - AI-detected search intent
    - Suggested titles based on intent/tone
    - LSI keywords from TF-IDF analysis
    - E-E-A-T optimization tips
    
    Can use existing research job data or generate fresh recommendations.
    Use regenerate_titles=true to get new title suggestions with different intent/tone.
    """
    tfidf_analysis = None
    competitor_data = None
    
    # Try to get data from research job if provided
    if request.job_id:
        try:
            result = await db.execute(
                select(ResearchArtifact)
                .where(
                    ResearchArtifact.job_id == request.job_id,
                    ResearchArtifact.type == "analysis_report",
                )
                .order_by(ResearchArtifact.created_at.desc())
                .limit(1)
            )
            artifact = result.scalar_one_or_none()
            if artifact and artifact.payload:
                tfidf_analysis = artifact.payload.get("tfidf_analysis")
                # Build competitor data from artifact
                competitors = artifact.payload.get("competitors", [])
                if competitors:
                    competitor_data = [
                        {"word_count": c.get("word_count", 0)} 
                        for c in competitors
                    ]
        except Exception:
            pass
    
    # Generate strategy pack
    pack = await strategy_service.generate_strategy_pack(
        keyword=request.keyword,
        market=request.market,
        tfidf_analysis=tfidf_analysis,
        competitor_data=competitor_data,
        intent=request.intent,
        tone=request.tone,
        regenerate_titles=request.regenerate_titles,
    )
    
    return pack


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


# ============ Draft Endpoints (Phase 3) ============


class DraftCreateRequest(BaseModel):
    """Request schema for creating a draft."""
    project_id: uuid.UUID
    keyword: str = Field(..., min_length=1, max_length=255)
    title: str = Field(default="")
    wizard_step: int = Field(default=1, ge=1, le=4)
    strategy_config: Optional[Dict[str, Any]] = None
    outline: Optional[Dict[str, Any]] = None
    research_job_id: Optional[uuid.UUID] = None


class DraftUpdateRequest(BaseModel):
    """Request schema for updating a draft."""
    title: Optional[str] = None
    wizard_step: Optional[int] = Field(default=None, ge=1, le=4)
    strategy_config: Optional[Dict[str, Any]] = None
    outline: Optional[Dict[str, Any]] = None
    content: Optional[str] = None
    word_count: Optional[int] = None
    secondary_keywords: Optional[List[str]] = None
    status: Optional[str] = None


class DraftResponse(BaseModel):
    """Response schema for draft operations."""
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    target_keyword: str
    wizard_step: Optional[int]
    status: str
    strategy_config: Optional[Dict[str, Any]]
    outline: Optional[Dict[str, Any]]
    content: Optional[str]
    word_count: int
    research_job_id: Optional[uuid.UUID]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class StreamRequest(BaseModel):
    """Request schema for streaming content generation."""
    title: str = Field(..., min_length=1)
    target_keyword: str = Field(..., min_length=1)
    outline: Dict[str, Any]
    secondary_keywords: List[str] = Field(default=[])
    tone: str = Field(default="professional")
    draft_id: Optional[uuid.UUID] = None


@router.post("/draft", status_code=status.HTTP_201_CREATED)
async def create_draft(
    request: DraftCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new article draft.
    
    Initializes a draft for the Strategy Wizard flow.
    """
    draft = await article_draft_service.create_draft(
        db,
        project_id=request.project_id,
        keyword=request.keyword,
        title=request.title,
        wizard_step=request.wizard_step,
        strategy_config=request.strategy_config,
        outline=request.outline,
        research_job_id=request.research_job_id,
    )
    
    return {
        "id": str(draft.id),
        "project_id": str(draft.project_id),
        "title": draft.title,
        "target_keyword": draft.target_keyword,
        "wizard_step": draft.wizard_step,
        "status": draft.status.value,
        "created_at": draft.created_at.isoformat(),
    }


@router.get("/draft/{draft_id}")
async def get_draft(
    draft_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a draft by ID.
    
    Returns full draft data for resuming wizard flow.
    """
    draft = await article_draft_service.get_draft(db, draft_id)
    
    if not draft:
        return {"error": "Draft not found"}, 404
    
    return {
        "id": str(draft.id),
        "project_id": str(draft.project_id),
        "title": draft.title,
        "target_keyword": draft.target_keyword,
        "wizard_step": draft.wizard_step,
        "status": draft.status.value,
        "strategy_config": draft.strategy_config,
        "outline": draft.outline,
        "content": draft.content,
        "word_count": draft.word_count,
        "research_job_id": str(draft.research_job_id) if draft.research_job_id else None,
        "secondary_keywords": draft.secondary_keywords,
        "created_at": draft.created_at.isoformat(),
        "updated_at": draft.updated_at.isoformat(),
    }


@router.patch("/draft/{draft_id}")
async def update_draft(
    draft_id: uuid.UUID,
    request: DraftUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a draft.
    
    Saves wizard progress at any step.
    """
    # Convert status string to enum if provided
    status_enum = None
    if request.status:
        try:
            status_enum = ArticleStatus(request.status)
        except ValueError:
            pass
    
    draft = await article_draft_service.update_draft(
        db,
        draft_id,
        title=request.title,
        wizard_step=request.wizard_step,
        strategy_config=request.strategy_config,
        outline=request.outline,
        content=request.content,
        word_count=request.word_count,
        secondary_keywords=request.secondary_keywords,
        status=status_enum,
    )
    
    if not draft:
        return {"error": "Draft not found"}, 404
    
    return {
        "id": str(draft.id),
        "title": draft.title,
        "wizard_step": draft.wizard_step,
        "status": draft.status.value,
        "updated_at": draft.updated_at.isoformat(),
    }


@router.delete("/draft/{draft_id}")
async def delete_draft(
    draft_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a draft.
    """
    deleted = await article_draft_service.delete_draft(db, draft_id)
    
    if not deleted:
        return {"error": "Draft not found"}, 404
    
    return {"message": "Draft deleted successfully"}


@router.get("/drafts")
async def list_drafts(
    project_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List drafts with optional filtering.
    """
    status_enum = None
    if status:
        try:
            status_enum = ArticleStatus(status)
        except ValueError:
            pass
    
    drafts = await article_draft_service.list_drafts(
        db,
        project_id=project_id,
        status=status_enum,
        limit=limit,
        offset=offset,
    )
    
    return {
        "drafts": [
            {
                "id": str(d.id),
                "title": d.title,
                "target_keyword": d.target_keyword,
                "wizard_step": d.wizard_step,
                "status": d.status.value,
                "word_count": d.word_count,
                "updated_at": d.updated_at.isoformat(),
            }
            for d in drafts
        ],
        "count": len(drafts),
    }


# ============ SSE Streaming Endpoint ============


@router.post("/generate-stream")
async def generate_content_stream(
    request: StreamRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate article content with SSE streaming.
    
    Streams progress and content events as sections are generated.
    Returns Server-Sent Events format.
    
    Events:
    - progress: {"section": "...", "progress": 0-100}
    - content: {"section": "...", "content": "..."}
    - done: {"total_words": N, "content": "..."}
    """
    # Build outline object from request
    sections = []
    for section_data in request.outline.get("sections", []):
        sections.append(OutlineSection(
            heading=section_data.get("heading", ""),
            level=section_data.get("level", 2),
            key_points=section_data.get("key_points", []),
            subsections=[],
        ))
    
    outline = ArticleOutline(
        title=request.title,
        meta_description=request.outline.get("meta_description", ""),
        sections=sections,
        estimated_word_count=request.outline.get("estimated_word_count", 2000),
        target_keywords=[request.target_keyword] + request.secondary_keywords,
    )
    
    async def event_generator():
        async for event in streaming_service.stream_article_content(
            outline=outline,
            target_keyword=request.target_keyword,
            secondary_keywords=request.secondary_keywords,
            tone=request.tone,
        ):
            yield event
        
        # If draft_id provided, update the draft with generated content
        # (This is handled on the client side for now)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
