"""
Research Background Tasks.

Celery tasks for keyword research and competitor analysis.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from celery import shared_task

from app.services.google_search import google_search_service
from app.services.crawler_service import crawler_service
from app.services.analysis_service import analysis_service
from app.services.cache_manager import cache_manager


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_keyword_task(
    self,
    task_id: str,
    keyword: str,
    market: str = "tw",
    depth: int = 10,
) -> dict:
    """
    Background task for complete keyword analysis.
    
    Steps:
    1. Fetch SERP results
    2. Crawl competitor pages
    3. Generate analysis report
    4. Cache results
    """
    import asyncio
    
    async def run_analysis():
        try:
            # Update task status
            await cache_manager.set(
                f"task:{task_id}",
                {"status": "processing", "progress": 10, "message": "Fetching SERP results..."},
                expire_days=1,
            )
            
            # Step 1: SERP
            serp_response = await google_search_service.search(
                keyword=keyword,
                market=market,
                num_results=depth,
            )
            
            await cache_manager.set(
                f"task:{task_id}",
                {"status": "processing", "progress": 30, "message": "Crawling competitors..."},
                expire_days=1,
            )
            
            # Step 2: Crawl
            urls = [r.url for r in serp_response.results]
            competitors = await crawler_service.crawl_pages(urls)
            
            await cache_manager.set(
                f"task:{task_id}",
                {"status": "processing", "progress": 70, "message": "Generating report..."},
                expire_days=1,
            )
            
            # Step 3: Analysis
            report = analysis_service.generate_report(
                keyword=keyword,
                market=market,
                competitors=competitors,
            )
            
            # Step 4: Cache
            cache_key = google_search_service.generate_cache_key(keyword, market)
            await cache_manager.set(f"report:{cache_key}", report.model_dump(), expire_days=7)
            
            # Mark complete
            result = {
                "status": "completed",
                "progress": 100,
                "message": "Analysis complete",
                "report": report.model_dump(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
            await cache_manager.set(f"task:{task_id}", result, expire_days=1)
            
            return result
            
        except Exception as e:
            error_result = {
                "status": "failed",
                "progress": 0,
                "message": str(e),
                "error": str(e),
            }
            await cache_manager.set(f"task:{task_id}", error_result, expire_days=1)
            raise
    
    # Run async code
    return asyncio.run(run_analysis())


@shared_task(bind=True)
def fetch_serp_task(self, keyword: str, market: str = "tw", num_results: int = 10) -> dict:
    """Simple SERP fetch task."""
    import asyncio
    
    async def fetch():
        response = await google_search_service.search(
            keyword=keyword,
            market=market,
            num_results=num_results,
        )
        return response.model_dump()
    
    return asyncio.run(fetch())
