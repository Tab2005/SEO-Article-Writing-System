"""
Topic Node Model.

Defines the TopicNode entity for representing the hierarchy of topics in the Topic Map.
"""

import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, DateTime, Text, ForeignKey, func, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.content_item import ContentItem
    from app.models.qualification_result import QualificationResult
    from app.models.article_brief import ArticleBrief


class TopicNode(Base):
    """TopicNode model representing nodes in the semantic topic tree."""
    
    __tablename__ = "topic_nodes"
    
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
    
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("topic_nodes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # role: pillar, supporting, bridge, comparison, decision, faq
    topic_role: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    journey_stage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    priority: Mapped[str] = mapped_column(String(50), default="medium", nullable=False) # high, medium, low
    
    supports: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    supported_by: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False) # draft, active, archived
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
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
        back_populates="topic_nodes",
    )
    
    parent: Mapped[Optional["TopicNode"]] = relationship(
        "TopicNode",
        remote_side=[id],
        back_populates="children",
    )
    
    children: Mapped[List["TopicNode"]] = relationship(
        "TopicNode",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    
    content_items: Mapped[List["ContentItem"]] = relationship(
        "ContentItem",
        back_populates="mapped_topic",
    )
    
    qualification_results: Mapped[List["QualificationResult"]] = relationship(
        "QualificationResult",
        back_populates="mapped_topic",
    )
    
    briefs: Mapped[List["ArticleBrief"]] = relationship(
        "ArticleBrief",
        back_populates="mapped_topic",
    )
    
    def __repr__(self) -> str:
        return f"<TopicNode {self.name} ({self.topic_role})>"
