"""
Research API Endpoints.

Handles keyword research and SERP analysis.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, status, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.dependencies import get_optional_current_user
from app.models.user import User
from app.models.research_job import ResearchJob, ResearchCompetitor
from app.schemas.research import (
    KeywordResearchRequest,
    SerpResponse,
    AnalysisReport,
    ResearchTaskCreate,
    ResearchTaskStatus,
    ResearchJobCreateRequest,
    ResearchJobResponse,
    ResearchCompetitorSummary,
    ResearchCompetitorContent,
)
from app.services import google_search_service, crawler_service, analysis_service
from app.services.research_job_service import create_job as create_research_job
from app.services.research_job_service import get_latest_artifact

router = APIRouter()


def _job_to_response(job: ResearchJob) -> ResearchJobResponse:
    return ResearchJobResponse(
        job_id=job.id,
        keyword=job.keyword,
        market=job.market,
        depth=job.depth,
        status=job.status,
        progress=job.progress,
        message=job.message,
        error=job.error,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


def _ensure_job_access(job: ResearchJob, user: Optional[User]) -> None:
    # If job is not bound to a user, allow access
    if job.user_id is None:
        return
    # If job is bound, require user
    if user is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Authentication required")
    # DevUser compatibility (has is_superuser)
    if getattr(user, "is_superuser", False):
        return
    if getattr(user, "id", None) != job.user_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Not allowed")


@router.post("/jobs", status_code=status.HTTP_202_ACCEPTED, response_model=ResearchJobResponse)
async def create_job_endpoint(
    request: ResearchJobCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Create a persistent research job and enqueue background execution."""
    try:
        print(f"Creating research job for keyword: {request.keyword}")
        user_id = getattr(current_user, "id", None) if current_user else None
        job = await create_research_job(
            db,
            keyword=request.keyword,
            market=request.market,
            depth=request.depth,
            user_id=user_id,
        )

        # Always use FastAPI BackgroundTasks for development
        from app.tasks.research_tasks import _run_research_job_async

        job.message = "Processing synchronously"
        # Run synchronously for now to avoid background task issues
        try:
            await _run_research_job_async(str(job.id))
        except Exception as e:
            print(f"Job execution failed: {e}")
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.now(timezone.utc)
        
        # background_tasks.add_task(run_job)

        await db.commit()
        await db.refresh(job)
        return _job_to_response(job)
    except Exception as e:
        print(f"Error creating research job: {e}")
        import traceback
        traceback.print_exc()
        raise


@router.get("/jobs", response_model=List[ResearchJobResponse])
async def list_jobs_endpoint(
    limit: int = 20,
    offset: int = 0,
    keyword: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """List research jobs with optional filtering.
    
    For authenticated users, returns only their jobs.
    For anonymous users, returns jobs without user_id.
    """
    query = select(ResearchJob).order_by(ResearchJob.created_at.desc())
    
    # Filter by user ownership
    if current_user:
        user_id = getattr(current_user, "id", None)
        if user_id and not getattr(current_user, "is_superuser", False):
            query = query.where(ResearchJob.user_id == user_id)
    else:
        # Anonymous: only show jobs without user_id
        query = query.where(ResearchJob.user_id.is_(None))
    
    # Optional keyword filter
    if keyword:
        query = query.where(ResearchJob.keyword.ilike(f"%{keyword}%"))
    
    # Optional status filter
    if status_filter:
        query = query.where(ResearchJob.status == status_filter)
    
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return [_job_to_response(job) for job in jobs]


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_endpoint(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Delete a research job and all its associated data."""
    job = await db.get(ResearchJob, job_id)
    if job is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    _ensure_job_access(job, current_user)
    
    await db.delete(job)
    await db.commit()
    return None


@router.get("/jobs/{job_id}", response_model=ResearchJobResponse)
async def get_job_endpoint(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    job = await db.get(ResearchJob, job_id)
    if job is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    _ensure_job_access(job, current_user)
    return _job_to_response(job)


@router.get("/jobs/{job_id}/report", response_model=AnalysisReport)
async def get_job_report_endpoint(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    job = await db.get(ResearchJob, job_id)
    if job is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    _ensure_job_access(job, current_user)

    artifact = await get_latest_artifact(db, job_id=job_id, artifact_type="analysis_report")
    if artifact is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Report not available")

    return AnalysisReport.model_validate(artifact.payload)


@router.get("/jobs/{job_id}/competitors", response_model=List[ResearchCompetitorSummary])
async def list_job_competitors_endpoint(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    job = await db.get(ResearchJob, job_id)
    if job is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    _ensure_job_access(job, current_user)

    result = await db.execute(
        select(ResearchCompetitor)
        .where(ResearchCompetitor.job_id == job_id)
        .order_by(ResearchCompetitor.rank.asc())
    )
    rows = result.scalars().all()
    return [
        ResearchCompetitorSummary(
            rank=r.rank,
            url=r.url,
            serp_title=r.serp_title,
            snippet=r.snippet,
            fetch_status=r.fetch_status,
            http_status=r.http_status,
            error=r.error,
            page_title=r.page_title,
            meta_description=r.meta_description,
            word_count=r.word_count,
            scraped_at=r.scraped_at,
            has_content=bool(r.content_text),
        )
        for r in rows
    ]


@router.get("/jobs/{job_id}/competitors/{rank}/content", response_model=ResearchCompetitorContent)
async def get_job_competitor_content_endpoint(
    job_id: uuid.UUID,
    rank: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    job = await db.get(ResearchJob, job_id)
    if job is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    _ensure_job_access(job, current_user)

    result = await db.execute(
        select(ResearchCompetitor).where(
            ResearchCompetitor.job_id == job_id,
            ResearchCompetitor.rank == rank,
        )
    )
    competitor = result.scalar_one_or_none()
    if competitor is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Competitor not found")
    if not competitor.content_text:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Content not available")

    return ResearchCompetitorContent(
        rank=competitor.rank,
        url=competitor.url,
        page_title=competitor.page_title,
        content_text=competitor.content_text,
        scraped_at=competitor.scraped_at,
    )


@router.post("/keyword", status_code=status.HTTP_202_ACCEPTED, response_model=ResearchTaskCreate)
async def submit_keyword_research(
    request: KeywordResearchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a keyword for research.
    
    Initiates background task for SERP fetching and competitor analysis.
    
    - **keyword**: Target keyword for research
    - **market**: Target market (e.g., 'tw', 'us')
    """
    task_id = str(uuid.uuid4())
    
    # For now, return immediately with task ID
    # Background task will be implemented in Task 10 (Celery)
    return ResearchTaskCreate(
        task_id=task_id,
        keyword=request.keyword,
        market=request.market,
        status="pending",
        message="Research task created. Use GET /research/{task_id} to check status.",
    )


@router.get("/serp", response_model=SerpResponse)
async def get_serp_results(
    keyword: str,
    market: str = "tw",
    num_results: int = 10,
):
    """
    Get SERP results directly (synchronous).
    
    Fetches Google search results for the given keyword.
    """
    response = await google_search_service.search(
        keyword=keyword,
        market=market,
        num_results=num_results,
    )
    return response


@router.get("/analyze", response_model=AnalysisReport)
async def analyze_keyword(
    keyword: str,
    market: str = "tw",
    depth: int = 10,
):
    """
    Perform complete keyword analysis (synchronous).
    
    Fetches SERP, crawls competitors, and generates report.
    Topic themes are NOT included - use POST /analyze-themes to get them.
    """
    # Step 1: Get SERP results
    serp_response = await google_search_service.search(
        keyword=keyword,
        market=market,
        num_results=depth,
    )
    
    # Step 2: Crawl competitor pages
    urls = [result.url for result in serp_response.results]
    competitors = await crawler_service.crawl_pages(urls)
    
    # Step 3: Generate analysis report (without topic themes)
    report = analysis_service.generate_report(
        keyword=keyword,
        market=market,
        competitors=competitors,
    )
    
    return report


@router.post("/analyze-themes")
async def analyze_topic_themes(
    request: dict,
):
    """
    Analyze competitor headings to extract semantic topic themes.
    
    This is a separate endpoint to be called on-demand after initial analysis.
    
    - **keyword**: Target keyword for context
    - **headings**: List of H2 heading lists, one per competitor
    """
    from app.services import llm_service
    from app.schemas.research import TopicTheme
    
    keyword = request.get("keyword", "")
    headings = request.get("headings", [])
    
    if not keyword or not headings:
        return {"topic_themes": [], "error": "Missing keyword or headings"}
    
    try:
        # Call LLM to analyze themes
        themes_data = await llm_service.extract_themes(
            headings_by_competitor=headings,
            keyword=keyword,
            top_n=8,
        )
        
        # Convert to TopicTheme objects
        topic_themes = [
            TopicTheme(
                theme_name=t.get("theme_name", ""),
                coverage_count=t.get("coverage_count", 0),
                total_competitors=t.get("total_competitors", len(headings)),
                example_headings=t.get("example_headings", []),
            )
            for t in themes_data
        ]
        
        return {"topic_themes": topic_themes}
    except Exception as e:
        return {"topic_themes": [], "error": str(e)}

@router.get("/{task_id}", response_model=ResearchTaskStatus)
async def get_research_result(task_id: str):
    """
    Get research results by task ID.
    
    Returns competitor analysis data if task is complete.
    """
    # TODO: Implement with database/Redis lookup in Task 10
    return ResearchTaskStatus(
        task_id=task_id,
        status="pending",
        progress=0,
        message="Task status tracking will be implemented with Celery",
        result=None,
        created_at=datetime.now(timezone.utc),
        completed_at=None,
    )


@router.get("/{task_id}/competitors")
async def get_competitor_details(task_id: str):
    """
    Get detailed competitor information.
    
    Returns scraped content structure for each competitor.
    """
    # TODO: Implement with database lookup
    return {"message": f"Competitor details for {task_id} - To be implemented with database"}


@router.post("/{task_id}/export")
async def export_research(task_id: str, format: str = "json"):
    """
    Export research results.
    
    Returns data in JSON or CSV format.
    """
    # TODO: Implement export functionality
    return {"message": f"Export research {task_id} as {format} - To be implemented"}
