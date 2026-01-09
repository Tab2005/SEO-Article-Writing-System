"""
Search Cache Model.

Caches SERP results to reduce API calls.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Text, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class SearchCache(Base):
    """Cache for Google SERP results."""
    
    __tablename__ = "search_cache"
    
    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Search Parameters
    keyword: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )
    market: Mapped[str] = mapped_column(
        String(10),
        default="tw",
        nullable=False,
    )
    
    # Cache Key (for quick lookup)
    cache_key: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    
    # Cached Data
    serp_results: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    competitor_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    analysis_report: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    
    # Statistics
    result_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    avg_word_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    
    def __repr__(self) -> str:
        return f"<SearchCache {self.keyword}>"
    
    @property
    def is_expired(self) -> bool:
        """Check if cache has expired."""
        return datetime.now(self.expires_at.tzinfo) > self.expires_at
