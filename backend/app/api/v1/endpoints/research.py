"""
Research API Endpoints.

Handles keyword research and SERP analysis.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, status, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.research import (
    KeywordResearchRequest,
    SerpResponse,
    AnalysisReport,
    ResearchTaskCreate,
    ResearchTaskStatus,
)
from app.services import google_search_service, crawler_service, analysis_service

router = APIRouter()


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
