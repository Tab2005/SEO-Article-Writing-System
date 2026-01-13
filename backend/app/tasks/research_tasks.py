"""
Research Background Tasks.

Celery tasks for keyword research and competitor analysis.
"""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

try:
    from celery import shared_task  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    def shared_task(*_args, **_kwargs):
        def _decorator(fn):
            return fn

        return _decorator
from sqlalchemy import select

from app.services.google_search import google_search_service
from app.services.crawler_service import crawler_service
from app.services.analysis_service import analysis_service
from app.services.cache_manager import cache_manager
from app.core.database import async_session_maker
from app.models.research_job import ResearchJob, ResearchCompetitor, ResearchArtifact


async def _set_job_state(
    job: ResearchJob,
    *,
    status: str,
    progress: int,
    message: str,
    error: Optional[str] = None,
) -> None:
    job.status = status
    job.progress = max(0, min(100, progress))
    job.message = message
    if error is not None:
        job.error = error
    if status == "running" and job.started_at is None:
        job.started_at = datetime.now(timezone.utc)
    if status in {"completed", "failed", "partial"}:
        job.completed_at = datetime.now(timezone.utc)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


async def _run_research_job_async(job_id: str) -> Dict[str, Any]:
    job_uuid = uuid.UUID(job_id)

    async with async_session_maker() as db:
        job = await db.get(ResearchJob, job_uuid)
        if job is None:
            print(f"Job {job_id} not found")
            return {"status": "failed", "message": "Job not found"}

        try:
            print(f"Starting research job {job_id} for keyword: {job.keyword}")
            await _set_job_state(job, status="running", progress=10, message="Fetching SERP results...")
            await db.commit()

            serp = await google_search_service.search(
                keyword=job.keyword,
                market=job.market,
                num_results=job.depth,
            )
            print(f"Fetched {len(serp.results)} SERP results")

            # Persist SERP snapshot
            for item in serp.results:
                result = await db.execute(
                    select(ResearchCompetitor).where(
                        ResearchCompetitor.job_id == job_uuid,
                        ResearchCompetitor.rank == item.rank,
                    )
                )
                competitor = result.scalar_one_or_none()
                if competitor is None:
                    competitor = ResearchCompetitor(
                        job_id=job_uuid,
                        rank=item.rank,
                        url=item.url,
                        serp_title=item.title,
                        snippet=item.snippet,
                        serp_fetched_at=item.scraped_at or serp.fetched_at,
                        fetch_status="pending",
                    )
                    db.add(competitor)
                else:
                    competitor.url = item.url
                    competitor.serp_title = item.title
                    competitor.snippet = item.snippet
                    competitor.serp_fetched_at = item.scraped_at or serp.fetched_at

            await db.commit()
            print("Persisted SERP results to database")

            await _set_job_state(job, status="running", progress=30, message="Crawling competitor pages...")
            await db.commit()

            urls = [r.url for r in serp.results]
            crawled = await crawler_service.crawl_pages(urls)

            # Map crawled results by URL
            crawled_by_url = {c.url: c for c in crawled}
            completed_count = 0
            total_count = len(urls) if urls else 1

            # Update competitor rows with crawled data
            for idx, url in enumerate(urls, start=1):
                result = await db.execute(
                    select(ResearchCompetitor).where(
                        ResearchCompetitor.job_id == job_uuid,
                        ResearchCompetitor.url == url,
                    )
                )
                competitor = result.scalar_one_or_none()
                if competitor is None:
                    continue

                c = crawled_by_url.get(url)
                if c is None:
                    competitor.fetch_status = "failed"
                    competitor.error = competitor.error or "Crawl failed"
                else:
                    competitor.fetch_status = "success"
                    competitor.page_title = c.title
                    competitor.meta_description = c.meta_description
                    competitor.meta_keywords = c.meta_keywords
                    competitor.headings = c.headings.model_dump()
                    competitor.word_count = c.word_count
                    competitor.scraped_at = c.scraped_at
                    if c.content_text:
                        competitor.content_text = c.content_text
                        competitor.content_hash = _hash_text(c.content_text)

                completed_count += 1
                job.progress = 30 + int(60 * (completed_count / total_count))
                job.message = f"Crawled {completed_count}/{total_count} pages"

                # Commit in batches to keep progress visible
                if idx % 3 == 0:
                    await db.commit()

            await db.commit()

            await _set_job_state(job, status="running", progress=max(job.progress, 90), message="Generating analysis report...")
            await db.commit()

            # Generate report from crawled results (content_text is used internally but stripped in report)
            report = analysis_service.generate_report(
                keyword=job.keyword,
                market=job.market,
                competitors=crawled,
                enable_tfidf=False,
            )

            artifact = ResearchArtifact(
                job_id=job_uuid,
                type="analysis_report",
                version=1,
                payload=report.model_dump(mode="json"),
            )
            db.add(artifact)

            # Final status: partial if too many failures
            success_count = sum(1 for c in crawled if c)
            if success_count == 0:
                await _set_job_state(job, status="failed", progress=0, message="No pages could be crawled", error="crawl_failed")
            elif success_count < max(1, int(total_count * 0.5)):
                await _set_job_state(job, status="partial", progress=100, message="Completed with partial crawl failures")
            else:
                await _set_job_state(job, status="completed", progress=100, message="Research completed")

            await db.commit()

            # Also cache a lightweight task status for quick polling
            await cache_manager.set(
                f"job:{job_id}",
                {
                    "status": job.status,
                    "progress": job.progress,
                    "message": job.message,
                    "completed_at": (job.completed_at.isoformat() if job.completed_at else None),
                },
                expire_days=1,
            )

            return {
                "status": job.status,
                "progress": job.progress,
                "message": job.message,
                "job_id": job_id,
            }

        except Exception as e:
            # If an exception happened during flush/commit, the session may be in a pending-rollback state.
            # Roll back first so we can persist the failed status.
            try:
                await db.rollback()
            except Exception:
                pass

            job = await db.get(ResearchJob, job_uuid) or job
            await _set_job_state(job, status="failed", progress=0, message="Research failed", error=str(e))
            await db.commit()
            await cache_manager.set(
                f"job:{job_id}",
                {"status": "failed", "progress": 0, "message": str(e)},
                expire_days=1,
            )
            raise


async def run_research_job(job_id: str) -> Dict[str, Any]:
    """Run research job in-process (usable by FastAPI BackgroundTasks).

    Note: Keep this async so it runs in the FastAPI event loop, avoiding
    cross-thread issues with the global async SQLAlchemy engine.
    """
    return await _run_research_job_async(job_id)


def run_research_job_sync(job_id: str) -> Dict[str, Any]:
    """Run research job from a sync context (e.g., Celery worker)."""
    import asyncio

    return asyncio.run(_run_research_job_async(job_id))


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def run_research_job_task(self, job_id: str) -> Dict[str, Any]:
    """Celery entrypoint for running a persistent research job."""
    return run_research_job_sync(job_id)


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
                enable_tfidf=False,
            )
            
            # Step 4: Cache
            cache_key = google_search_service.generate_cache_key(keyword, market)
            await cache_manager.set(f"report:{cache_key}", report.model_dump(mode="json"), expire_days=7)
            
            # Mark complete
            result = {
                "status": "completed",
                "progress": 100,
                "message": "Analysis complete",
                "report": report.model_dump(mode="json"),
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
