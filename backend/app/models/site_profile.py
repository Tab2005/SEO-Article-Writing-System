"""
Site Profile Model.

Defines the SiteProfile entity for storing website identity and positioning rules.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

def utc_now():
    return datetime.now(timezone.utc)

from sqlalchemy import String, DateTime, Text, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project


class SiteProfile(Base):
    """SiteProfile model for storing SEO identity configuration."""
    
    __tablename__ = "site_profiles"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    
    site_name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    site_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # JSON arrays or objects
    target_audiences: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    products_or_services: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    core_topics: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    allowed_angles: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    restricted_angles: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    brand_voice: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proof_assets: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    primary_goals: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    geo_focus: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    industry_constraints: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    editorial_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    summary_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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
        back_populates="site_profile",
    )
    
    def __repr__(self) -> str:
        return f"<SiteProfile {self.site_name} (Project: {self.project_id})>"
