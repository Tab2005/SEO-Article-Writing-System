"""
Qualification Result Model.

Defines the QualificationResult entity for representing evaluation decisions on candidate search terms.
"""

import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, Text, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.topic_node import TopicNode


class QualificationResult(Base):
    """QualificationResult model storing evaluation status for content ideas."""
    
    __tablename__ = "qualification_results"
    
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
    
    input_term: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Decision: qualified, rewrite_existing, not_qualified
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    summary_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    mapped_topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("topic_nodes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    suggested_angle: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_journey_stage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Fits: High, Medium, Low
    identity_fit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    topic_fit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    audience_fit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    authority_fit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    business_fit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Risks: High, Medium, Low, None
    overlap_risk: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    boundary_risk: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    risks: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    alternative_topics: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    recommended_next_step: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # review_status: generated, approved, rejected, edited
    review_status: Mapped[str] = mapped_column(String(50), default="generated", nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="qualification_results",
    )
    
    mapped_topic: Mapped[Optional["TopicNode"]] = relationship(
        "TopicNode",
        back_populates="qualification_results",
    )
    
    def __repr__(self) -> str:
        return f"<QualificationResult {self.input_term} ({self.decision})>"
