"""
Content API Endpoints.

Handles AI-powered content generation.
"""

from typing import Optional, List, Dict, Any
import uuid

from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.research_job import ResearchArtifact
from app.models.article import Article, ArticleStatus
from app.models.article_brief import ArticleBrief
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
from app.services.brief_service import brief_service
from app.services.qa_service import qa_service

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
    brief_id: Optional[uuid.UUID] = None


class ContentRequest(BaseModel):
    """Request schema for full content generation."""
    topic: str = Field(..., min_length=1, max_length=500)
    target_keyword: str = Field(..., min_length=1, max_length=255)
    secondary_keywords: List[str] = Field(default=[], max_length=10)
    word_count_target: int = Field(default=2000, ge=500, le=10000)
    tone: str = Field(default="professional")
    market: str = Field(default="tw")
    research_job_id: Optional[uuid.UUID] = None
    brief_id: Optional[uuid.UUID] = None
    outline: Optional[ArticleOutline] = None


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
    
    brief_data = None
    if request.brief_id:
        result = await db.execute(select(ArticleBrief).where(ArticleBrief.id == request.brief_id))
        brief_data = result.scalar_one_or_none()

    outline = await llm_service.generate_outline(
        topic=request.topic,
        target_keyword=request.target_keyword,
        secondary_keywords=request.secondary_keywords,
        competitor_h2s=competitor_h2s,
        word_count_target=request.word_count_target,
        tone=request.tone,
        brief_data=brief_data,
    )
    
    return outline


@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_content(request: ContentRequest, db: AsyncSession = Depends(get_db)):
    """
    Generate full article content.
    
    Creates complete article based on topic and keywords.
    Includes competitor analysis for SEO optimization.
    """
    # Auto-backup existing draft if it already has content
    if request.brief_id:
        result = await db.execute(
            select(Article)
            .where(Article.brief_id == request.brief_id, Article.parent_version_id == None)
        )
        existing_draft = result.scalar_one_or_none()
        if existing_draft and existing_draft.content:
            await article_draft_service.create_draft_version(db, existing_draft.id)

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
    
    brief_data = None
    if request.brief_id:
        result = await db.execute(select(ArticleBrief).where(ArticleBrief.id == request.brief_id))
        brief_data = result.scalar_one_or_none()

    # Step 2: Generate outline
    if request.outline:
        outline = request.outline
    else:
        outline = await llm_service.generate_outline(
            topic=request.topic,
            target_keyword=request.target_keyword,
            secondary_keywords=request.secondary_keywords,
            competitor_h2s=competitor_h2s,
            word_count_target=request.word_count_target,
            tone=request.tone,
            brief_data=brief_data,
        )
    
    # Step 3: Generate full content
    content = await llm_service.generate_full_article(
        outline=outline,
        target_keyword=request.target_keyword,
        secondary_keywords=request.secondary_keywords,
        brief_data=brief_data,
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
    brief_id: Optional[uuid.UUID] = None


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
    brief_id: Optional[uuid.UUID] = None
    qa_status: Optional[str] = None
    qa_results: Optional[Dict[str, Any]] = None


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
    brief_id: Optional[uuid.UUID] = None
    qa_status: Optional[str] = None
    qa_results: Optional[Dict[str, Any]] = None
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
    if request.brief_id:
        brief = await brief_service.get_brief(db, request.brief_id)
        if not brief:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article brief not found.")
        if brief.status != "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="文章任務書尚未被核准 (Article brief has not been approved)."
            )

    draft = await article_draft_service.create_draft(
        db,
        project_id=request.project_id,
        keyword=request.keyword,
        title=request.title,
        wizard_step=request.wizard_step,
        strategy_config=request.strategy_config,
        outline=request.outline,
        research_job_id=request.research_job_id,
        brief_id=request.brief_id,
    )
    
    return {
        "id": str(draft.id),
        "project_id": str(draft.project_id),
        "title": draft.title,
        "target_keyword": draft.target_keyword,
        "wizard_step": draft.wizard_step,
        "status": draft.status.value,
        "brief_id": str(draft.brief_id) if draft.brief_id else None,
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
        "brief_id": str(draft.brief_id) if draft.brief_id else None,
        "qa_status": draft.qa_status,
        "qa_results": draft.qa_results,
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
    if request.brief_id:
        brief = await brief_service.get_brief(db, request.brief_id)
        if not brief:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article brief not found.")
        if brief.status != "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="文章任務書尚未被核准 (Article brief has not been approved)."
            )

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
        brief_id=request.brief_id,
        qa_status=request.qa_status,
        qa_results=request.qa_results,
    )
    
    if not draft:
        return {"error": "Draft not found"}, 404
    
    return {
        "id": str(draft.id),
        "title": draft.title,
        "wizard_step": draft.wizard_step,
        "status": draft.status.value,
        "brief_id": str(draft.brief_id) if draft.brief_id else None,
        "qa_status": draft.qa_status,
        "qa_results": draft.qa_results,
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
                "brief_id": str(d.brief_id) if d.brief_id else None,
                "qa_status": d.qa_status,
                "updated_at": d.updated_at.isoformat(),
            }
            for d in drafts
        ],
        "count": len(drafts),
    }


@router.post("/draft/{draft_id}/qa")
async def run_draft_qa(
    draft_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Run QA Gate V1 check on a draft.
    """
    article = await qa_service.run_qa(db, draft_id)
    return {
        "id": str(article.id),
        "qa_status": article.qa_status,
        "qa_results": article.qa_results,
        "updated_at": article.updated_at.isoformat(),
    }


@router.post("/draft/{draft_id}/save-version")
async def save_draft_version(
    draft_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a backup of the current draft.
    """
    backup = await article_draft_service.create_draft_version(db, draft_id)
    if not backup:
        raise HTTPException(status_code=404, detail="Draft not found or is already a historical version.")
    return {
        "message": "Draft version saved successfully",
        "backup_id": str(backup.id),
        "version": backup.version
    }


@router.get("/draft/{draft_id}/versions")
async def list_draft_versions(
    draft_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get history versions of the draft.
    """
    versions = await article_draft_service.list_draft_versions(db, draft_id)
    return [
        {
            "id": str(v.id),
            "version": v.version,
            "title": v.title,
            "word_count": v.word_count,
            "status": v.status.value,
            "qa_status": v.qa_status,
            "created_at": v.created_at.isoformat(),
            "updated_at": v.updated_at.isoformat(),
        }
        for v in versions
    ]


@router.post("/draft/{draft_id}/versions/{version_id}/rollback")
async def rollback_draft_version(
    draft_id: uuid.UUID,
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Rollback the main draft to a historical version.
    """
    draft = await article_draft_service.rollback_to_version(db, draft_id, version_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft or target version not found.")
    return {
        "message": "Draft rolled back successfully",
        "id": str(draft.id),
        "title": draft.title,
        "content": draft.content,
        "outline": draft.outline,
        "version": draft.version,
        "updated_at": draft.updated_at.isoformat()
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
