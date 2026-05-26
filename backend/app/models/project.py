"""
Project Model.

Defines the Project entity for organizing articles and research.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING

def utc_now():
    return datetime.now(timezone.utc)

from sqlalchemy import String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.article import Article
    from app.models.site_profile import SiteProfile
    from app.models.topic_node import TopicNode
    from app.models.content_item import ContentItem
    from app.models.qualification_result import QualificationResult
    from app.models.article_brief import ArticleBrief


class Project(Base):
    """Project model for organizing SEO content."""
    
    __tablename__ = "projects"
    
    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Foreign Key
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Project Info
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Target Market
    target_market: Mapped[str] = mapped_column(
        String(10),
        default="tw",
        nullable=False,
    )
    
    # New planning fields
    mode: Mapped[str] = mapped_column(
        String(50),
        default="existing_site",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        nullable=False,
    )
    domain: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        onupdate=utc_now,
        nullable=False,
    )
    
    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="projects",
    )
    articles: Mapped[List["Article"]] = relationship(
        "Article",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    site_profile: Mapped[Optional["SiteProfile"]] = relationship(
        "SiteProfile",
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=False,
    )
    topic_nodes: Mapped[List["TopicNode"]] = relationship(
        "TopicNode",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    content_items: Mapped[List["ContentItem"]] = relationship(
        "ContentItem",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    qualification_results: Mapped[List["QualificationResult"]] = relationship(
        "QualificationResult",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    briefs: Mapped[List["ArticleBrief"]] = relationship(
        "ArticleBrief",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Project {self.name}>"
