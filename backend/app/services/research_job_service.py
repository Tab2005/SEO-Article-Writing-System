"""Research Job Service.

Creates and manages persistent research jobs stored in the database.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.research_job import ResearchArtifact, ResearchCompetitor, ResearchJob
from app.services.runtime_settings import get_ai_config, get_google_search_config


def _mask_secret(secret: Optional[str]) -> Optional[str]:
	if not secret:
		return None
	if len(secret) <= 8:
		return "***"
	return f"***{secret[-4:]}"


async def build_settings_snapshot() -> Dict[str, Any]:
	google_api_key, google_cx_id = await get_google_search_config()
	ai_provider, ai_model, ai_api_key = await get_ai_config()

	return {
		"google": {
			"configured": bool(google_api_key and google_cx_id),
			"api_key": _mask_secret(google_api_key),
			"cx_id": _mask_secret(google_cx_id),
		},
		"ai": {
			"provider": ai_provider,
			"model": ai_model,
			"configured": bool(ai_api_key),
			"api_key": _mask_secret(ai_api_key),
		},
		"captured_at": datetime.now(timezone.utc).isoformat(),
	}


async def create_job(
	db: AsyncSession,
	*,
	keyword: str,
	market: str,
	depth: int,
	user_id: Optional[uuid.UUID] = None,
) -> ResearchJob:
	job = ResearchJob(
		user_id=user_id,
		keyword=keyword,
		market=market,
		depth=depth,
		status="pending",
		progress=0,
		message="Queued",
		settings_snapshot=await build_settings_snapshot(),
	)
	db.add(job)
	await db.flush()
	return job


async def get_job(db: AsyncSession, job_id: uuid.UUID) -> Optional[ResearchJob]:
	return await db.get(ResearchJob, job_id)


async def get_latest_artifact(
	db: AsyncSession,
	*,
	job_id: uuid.UUID,
	artifact_type: str,
) -> Optional[ResearchArtifact]:
	result = await db.execute(
		select(ResearchArtifact)
		.where(ResearchArtifact.job_id == job_id, ResearchArtifact.type == artifact_type)
		.order_by(ResearchArtifact.created_at.desc())
		.limit(1)
	)
	return result.scalar_one_or_none()


async def upsert_competitor_serp(
	db: AsyncSession,
	*,
	job_id: uuid.UUID,
	rank: int,
	url: str,
	serp_title: str,
	snippet: str,
	fetched_at: datetime,
) -> ResearchCompetitor:
	result = await db.execute(
		select(ResearchCompetitor).where(
			ResearchCompetitor.job_id == job_id,
			ResearchCompetitor.rank == rank,
		)
	)
	competitor = result.scalar_one_or_none()
	if competitor is None:
		competitor = ResearchCompetitor(
			job_id=job_id,
			rank=rank,
			url=url,
			serp_title=serp_title,
			snippet=snippet,
			serp_fetched_at=fetched_at,
			fetch_status="pending",
		)
		db.add(competitor)
		await db.flush()
		return competitor

	competitor.url = url
	competitor.serp_title = serp_title
	competitor.snippet = snippet
	competitor.serp_fetched_at = fetched_at
	return competitor