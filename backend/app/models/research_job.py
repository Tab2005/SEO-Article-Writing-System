"""Research Job Models.

Provides persistent keyword research jobs with:
- SERP snapshot
- Crawled competitor page content
- Analysis artifacts (e.g., AnalysisReport)

These tables enable reusing research results later for content generation.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ResearchJob(Base):
	__tablename__ = "research_jobs"

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

	user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
		UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
	)

	keyword: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
	market: Mapped[str] = mapped_column(String(10), nullable=False, default="tw")
	depth: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

	status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
	progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
	message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
	error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

	settings_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), nullable=False
	)
	started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
	completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

	competitors: Mapped[List["ResearchCompetitor"]] = relationship(
		"ResearchCompetitor",
		back_populates="job",
		cascade="all, delete-orphan",
		order_by="ResearchCompetitor.rank",
	)

	artifacts: Mapped[List["ResearchArtifact"]] = relationship(
		"ResearchArtifact",
		back_populates="job",
		cascade="all, delete-orphan",
		order_by="ResearchArtifact.created_at",
	)


class ResearchCompetitor(Base):
	__tablename__ = "research_competitors"

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

	job_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), ForeignKey("research_jobs.id"), nullable=False, index=True
	)

	rank: Mapped[int] = mapped_column(Integer, nullable=False)
	url: Mapped[str] = mapped_column(Text, nullable=False)

	serp_title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
	snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
	serp_fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

	fetch_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
	http_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
	error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

	page_title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
	meta_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
	meta_keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
	headings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

	word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
	content_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
	content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

	scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

	job: Mapped[ResearchJob] = relationship("ResearchJob", back_populates="competitors")


Index(
	"ix_research_competitors_job_rank",
	ResearchCompetitor.job_id,
	ResearchCompetitor.rank,
	unique=True,
)


class ResearchArtifact(Base):
	__tablename__ = "research_artifacts"

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

	job_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), ForeignKey("research_jobs.id"), nullable=False, index=True
	)

	type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
	version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
	payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), nullable=False
	)

	job: Mapped[ResearchJob] = relationship("ResearchJob", back_populates="artifacts")