"""
Project model for organizing SEO content and campaigns.

This model handles:
- Project management for SEO campaigns
- Keyword tracking and management
- Article organization
- Project analytics and reporting
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from typing import Optional
import enum

from app.database import Base

class ProjectStatus(enum.Enum):
    """Project status enumeration."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class Project(Base):
    """Project model for organizing SEO content and campaigns."""
    
    __tablename__ = "projects"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()), index=True)
    
    # Basic information
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    website_url = Column(String(500), nullable=True)
    
    # Status and configuration
    status = Column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE, nullable=False, index=True)
    
    # SEO settings
    target_language = Column(String(10), default="zh-TW", nullable=False)
    target_country = Column(String(5), default="TW", nullable=False)
    
    # Keywords and content strategy
    primary_keywords = Column(JSON, default=list, nullable=False)  # List of main keywords
    secondary_keywords = Column(JSON, default=list, nullable=False)  # List of supporting keywords
    competitor_urls = Column(JSON, default=list, nullable=False)  # Competitor analysis
    content_strategy = Column(JSON, default=dict, nullable=False)  # Content planning settings
    
    # Analytics and tracking
    total_articles = Column(Integer, default=0, nullable=False)
    published_articles = Column(Integer, default=0, nullable=False)
    draft_articles = Column(Integer, default=0, nullable=False)
    
    # Project metrics
    avg_word_count = Column(Integer, default=0, nullable=False)
    total_search_volume = Column(Integer, default=0, nullable=False)
    estimated_traffic = Column(Integer, default=0, nullable=False)
    
    # Settings and preferences
    writing_style = Column(JSON, default=dict, nullable=False)  # Writing guidelines
    seo_settings = Column(JSON, default=dict, nullable=False)  # SEO preferences
    ai_settings = Column(JSON, default=dict, nullable=False)  # AI generation settings
    
    # Foreign keys
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="projects")
    articles = relationship("Article", back_populates="project", cascade="all, delete-orphan")
    search_caches = relationship("SearchCache", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status.value}')>"
    
    def to_dict(self, include_articles: bool = False) -> dict:
        """Convert project to dictionary."""
        data = {
            "id": self.id,  # Already string
            "name": self.name,
            "description": self.description,
            "website_url": self.website_url,
            "status": self.status.value,
            "target_language": self.target_language,
            "target_country": self.target_country,
            "primary_keywords": self.primary_keywords,
            "secondary_keywords": self.secondary_keywords,
            "competitor_urls": self.competitor_urls,
            "content_strategy": self.content_strategy,
            "total_articles": self.total_articles,
            "published_articles": self.published_articles,
            "draft_articles": self.draft_articles,
            "avg_word_count": self.avg_word_count,
            "total_search_volume": self.total_search_volume,
            "estimated_traffic": self.estimated_traffic,
            "writing_style": self.writing_style,
            "seo_settings": self.seo_settings,
            "ai_settings": self.ai_settings,
            "user_id": self.user_id,  # Already string
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
        }
        
        if include_articles and self.articles:
            data["articles"] = [article.to_dict(include_content=False) for article in self.articles]
        
        return data
    
    @property
    def completion_rate(self) -> float:
        """Calculate project completion rate based on articles."""
        if self.total_articles == 0:
            return 0.0
        return (self.published_articles / self.total_articles) * 100
    
    @property
    def is_active(self) -> bool:
        """Check if project is in active status."""
        return self.status == ProjectStatus.ACTIVE
    
    def update_article_counts(self):
        """Update article count statistics."""
        if self.articles:
            self.total_articles = len(self.articles)
            self.published_articles = len([a for a in self.articles if a.status == "published"])
            self.draft_articles = len([a for a in self.articles if a.status == "draft"])
            
            # Update average word count
            word_counts = [a.word_count for a in self.articles if a.word_count > 0]
            self.avg_word_count = sum(word_counts) // len(word_counts) if word_counts else 0
    
    def add_keyword(self, keyword: str, is_primary: bool = True):
        """Add a keyword to the project."""
        keywords = self.primary_keywords if is_primary else self.secondary_keywords
        
        if keyword.lower() not in [k.lower() for k in keywords]:
            keywords.append(keyword)
            
            if is_primary:
                self.primary_keywords = keywords
            else:
                self.secondary_keywords = keywords
    
    def remove_keyword(self, keyword: str, is_primary: bool = True):
        """Remove a keyword from the project."""
        keywords = self.primary_keywords if is_primary else self.secondary_keywords
        
        # Case-insensitive removal
        keywords = [k for k in keywords if k.lower() != keyword.lower()]
        
        if is_primary:
            self.primary_keywords = keywords
        else:
            self.secondary_keywords = keywords
    
    def add_competitor(self, url: str):
        """Add a competitor URL."""
        if url not in self.competitor_urls:
            self.competitor_urls.append(url)
    
    def remove_competitor(self, url: str):
        """Remove a competitor URL."""
        self.competitor_urls = [u for u in self.competitor_urls if u != url]
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def get_all_keywords(self) -> list:
        """Get all keywords (primary + secondary) for the project."""
        return self.primary_keywords + self.secondary_keywords
    
    def get_writing_guidelines(self) -> dict:
        """Get writing style guidelines with defaults."""
        default_style = {
            "tone": "professional",
            "length": "medium",  # short, medium, long
            "structure": "standard",  # standard, listicle, howto
            "include_faq": True,
            "include_conclusion": True,
            "min_word_count": 800,
            "max_word_count": 2000,
        }
        
        return {**default_style, **self.writing_style}
    
    def get_seo_guidelines(self) -> dict:
        """Get SEO settings with defaults."""
        default_seo = {
            "keyword_density": 2.0,  # Target keyword density percentage
            "meta_description_length": 155,
            "title_length": 60,
            "include_schema": True,
            "optimize_images": True,
            "internal_links": 3,  # Minimum internal links
            "external_links": 2,  # Minimum external links
        }
        
        return {**default_seo, **self.seo_settings}

# Add relationship to User model
from app.models.user import User
User.projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")