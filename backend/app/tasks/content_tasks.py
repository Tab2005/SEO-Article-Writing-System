"""
Content Generation Background Tasks.

Celery tasks for AI content generation.
"""

import uuid
from datetime import datetime, timezone

from celery import shared_task

from app.services.llm_service import llm_service
from app.services.cache_manager import cache_manager
from app.services.google_search import google_search_service
from app.services.crawler_service import crawler_service
from app.services.analysis_service import analysis_service


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def generate_article_task(
    self,
    task_id: str,
    topic: str,
    target_keyword: str,
    word_count_target: int = 2000,
    tone: str = "professional",
    market: str = "tw",
    use_competitor_analysis: bool = True,
) -> dict:
    """
    Background task for full article generation.
    
    Steps:
    1. (Optional) Analyze competitors
    2. Generate outline
    3. Generate content
    4. Store result
    """
    import asyncio
    
    async def generate():
        try:
            competitor_h2s = None
            
            await cache_manager.set(
                f"task:{task_id}",
                {"status": "processing", "progress": 10, "message": "Analyzing competitors..."},
                expire_days=1,
            )
            
            if use_competitor_analysis:
                try:
                    serp = await google_search_service.search(
                        keyword=target_keyword,
                        market=market,
                        num_results=5,
                    )
                    urls = [r.url for r in serp.results]
                    competitors = await crawler_service.crawl_pages(urls)
                    competitor_h2s = analysis_service.extract_common_headings(competitors, "h2", 10)
                except Exception:
                    pass  # Continue without competitor analysis
            
            await cache_manager.set(
                f"task:{task_id}",
                {"status": "processing", "progress": 30, "message": "Generating outline..."},
                expire_days=1,
            )
            
            # Generate outline
            outline = await llm_service.generate_outline(
                topic=topic,
                target_keyword=target_keyword,
                competitor_h2s=competitor_h2s,
                word_count_target=word_count_target,
                tone=tone,
            )
            
            await cache_manager.set(
                f"task:{task_id}",
                {"status": "processing", "progress": 60, "message": "Writing content..."},
                expire_days=1,
            )
            
            # Generate full content
            content = await llm_service.generate_full_article(
                outline=outline,
                target_keyword=target_keyword,
            )
            
            # Store result
            result = {
                "status": "completed",
                "progress": 100,
                "message": "Content generated successfully",
                "outline": outline.model_dump(),
                "content": content,
                "word_count": len(content),
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
    
    return asyncio.run(generate())


@shared_task(bind=True)
def optimize_content_task(
    self,
    task_id: str,
    content: str,
    target_keywords: list[str],
) -> dict:
    """Background task for content optimization."""
    import asyncio
    
    async def optimize():
        try:
            await cache_manager.set(
                f"task:{task_id}",
                {"status": "processing", "progress": 50, "message": "Optimizing..."},
                expire_days=1,
            )
            
            optimized = await llm_service.optimize_content(content, target_keywords)
            
            result = {
                "status": "completed",
                "progress": 100,
                "message": "Optimization complete",
                "content": optimized,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
            await cache_manager.set(f"task:{task_id}", result, expire_days=1)
            
            return result
            
        except Exception as e:
            error_result = {"status": "failed", "message": str(e)}
            await cache_manager.set(f"task:{task_id}", error_result, expire_days=1)
            raise
    
    return asyncio.run(optimize())
