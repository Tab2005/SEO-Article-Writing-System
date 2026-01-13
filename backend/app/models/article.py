"""
Article Model.

Defines the Article entity with version control.
"""

import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import JSON, String, DateTime, Text, Integer, ForeignKey, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
import enum

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project


class ArticleStatus(str, enum.Enum):
    """Article status enum."""
    DRAFT = "draft"
    GENERATING = "generating"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Article(Base):
    """Article model with versioning support."""
    
    __tablename__ = "articles"
    
    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Foreign Key
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Article Info
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    slug: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        index=True,
    )
    
    # Content
    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    outline: Mapped[Optional[dict]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    
    # SEO Metadata
    target_keyword: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    secondary_keywords: Mapped[Optional[list]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    meta_description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    
    # Strategy Wizard Config (Phase 3)
    strategy_config: Mapped[Optional[dict]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
        comment="Stores intent, tone, lsi_keywords, suggested_titles from wizard",
    )
    research_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Links to the research job used for this article",
    )
    wizard_step: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Current wizard step (1-4) for draft resumption",
    )
    
    # Statistics
    word_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    
    # Version Control
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    parent_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    # Status
    status: Mapped[ArticleStatus] = mapped_column(
        Enum(ArticleStatus),
        default=ArticleStatus.DRAFT,
        nullable=False,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="articles",
    )
    
    def __repr__(self) -> str:
        return f"<Article {self.title[:50]}>"
