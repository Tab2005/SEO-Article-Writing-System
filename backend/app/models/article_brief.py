"""
Article Brief Model.

Defines the ArticleBrief entity representing the structured content planning brief.
"""

import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.qualification_result import QualificationResult
    from app.models.topic_node import TopicNode
    from app.models.article import Article


class ArticleBrief(Base):
    """ArticleBrief model representing an article writing blueprint."""

    __tablename__ = "article_briefs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    qualification_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("qualification_results.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    mapped_topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("topic_nodes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title_direction: Mapped[str] = mapped_column(String(500), nullable=False)
    article_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    search_intent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    target_audience: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    primary_question: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_question: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    info_gain_requirement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    restricted_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    recommended_internal_links: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cta_direction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # status: draft, approved, completed
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default=func.now(),
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="briefs",
    )

    qualification: Mapped[Optional["QualificationResult"]] = relationship(
        "QualificationResult",
    )

    mapped_topic: Mapped[Optional["TopicNode"]] = relationship(
        "TopicNode",
        back_populates="briefs",
    )

    articles: Mapped[List["Article"]] = relationship(
        "Article",
        back_populates="brief",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ArticleBrief {self.title_direction[:50]} ({self.status})>"
