"""
Content Item Model.

Defines the ContentItem entity representing existing/imported articles mapped to the topic map.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

def utc_now():
    return datetime.now(timezone.utc)

from sqlalchemy import String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.topic_node import TopicNode


class ContentItem(Base):
    """ContentItem model representing imported or existing articles on the domain."""
    
    __tablename__ = "content_items"
    
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
    
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    content_type: Mapped[str] = mapped_column(String(50), default="article", nullable=False) # article, landing_page, etc.
    
    mapped_topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("topic_nodes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    journey_stage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # awareness, consideration, decision
    status: Mapped[str] = mapped_column(String(50), default="imported", nullable=False) # imported, mapped, archived
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="content_items",
    )
    
    mapped_topic: Mapped[Optional["TopicNode"]] = relationship(
        "TopicNode",
        back_populates="content_items",
    )
    
    def __repr__(self) -> str:
        return f"<ContentItem {self.title}>"
