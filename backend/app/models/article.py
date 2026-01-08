"""
Article model for managing SEO content.

This model handles:
- Article content and metadata
- SEO optimization data
- Publishing status and workflow
- Performance analytics
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Enum, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from typing import Optional, Dict, List
import enum

from app.database import Base

class ArticleStatus(enum.Enum):
    """Article status enumeration."""
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class ArticleType(enum.Enum):
    """Article type enumeration."""
    BLOG_POST = "blog_post"
    PRODUCT_PAGE = "product_page"
    LANDING_PAGE = "landing_page"
    FAQ = "faq"
    GUIDE = "guide"
    NEWS = "news"

class Article(Base):
    """Article model for managing SEO content."""
    
    __tablename__ = "articles"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()), index=True)
    
    # Basic information
    title = Column(String(500), nullable=False, index=True)
    slug = Column(String(200), nullable=False, index=True)
    excerpt = Column(Text, nullable=True)
    
    # Content
    content = Column(Text, nullable=True)  # Main article content
    html_content = Column(Text, nullable=True)  # Processed HTML content
    
    # Article metadata
    status = Column(Enum(ArticleStatus), default=ArticleStatus.DRAFT, nullable=False, index=True)
    article_type = Column(Enum(ArticleType), default=ArticleType.BLOG_POST, nullable=False)
    language = Column(String(10), default="zh-TW", nullable=False)
    
    # SEO fields
    meta_title = Column(String(200), nullable=True)
    meta_description = Column(String(500), nullable=True)
    meta_keywords = Column(JSON, default=list, nullable=False)  # List of keywords
    
    # Content analysis
    word_count = Column(Integer, default=0, nullable=False)
    reading_time = Column(Integer, default=0, nullable=False)  # in minutes
    
    # Target keywords and optimization
    primary_keyword = Column(String(200), nullable=True, index=True)
    secondary_keywords = Column(JSON, default=list, nullable=False)
    keyword_density = Column(Float, default=0.0, nullable=False)
    
    # SEO scores and analysis
    seo_score = Column(Float, default=0.0, nullable=False)  # Overall SEO score (0-100)
    readability_score = Column(Float, default=0.0, nullable=False)  # Readability score
    
    # Content structure
    headings = Column(JSON, default=list, nullable=False)  # H1, H2, H3 structure
    images = Column(JSON, default=list, nullable=False)  # Image data with alt texts
    links = Column(JSON, default=dict, nullable=False)  # Internal and external links
    
    # AI generation metadata
    ai_prompt = Column(Text, nullable=True)  # Prompt used to generate content
    ai_model = Column(String(100), nullable=True)  # AI model used
    generation_settings = Column(JSON, default=dict, nullable=False)
    
    # Publishing information
    published_at = Column(DateTime(timezone=True), nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    
    # External publishing
    wordpress_id = Column(String(50), nullable=True)  # WordPress post ID if synced
    external_url = Column(String(1000), nullable=True)  # Published URL
    
    # Analytics and performance
    views = Column(Integer, default=0, nullable=False)
    shares = Column(Integer, default=0, nullable=False)
    engagement_score = Column(Float, default=0.0, nullable=False)
    
    # Search performance
    avg_ranking = Column(Float, nullable=True)  # Average keyword ranking
    search_impressions = Column(Integer, default=0, nullable=False)
    search_clicks = Column(Integer, default=0, nullable=False)
    ctr = Column(Float, default=0.0, nullable=False)  # Click-through rate
    
    # Content optimization suggestions
    suggestions = Column(JSON, default=list, nullable=False)  # AI suggestions for improvement
    
    # Foreign keys
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="articles")
    user = relationship("User", back_populates="articles")
    
    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}...', status='{self.status.value}')>"
    
    def to_dict(self, include_content: bool = True, include_analytics: bool = False) -> dict:
        """Convert article to dictionary."""
        data = {
            "id": self.id,  # Already string
            "title": self.title,
            "slug": self.slug,
            "excerpt": self.excerpt,
            "status": self.status.value,
            "article_type": self.article_type.value,
            "language": self.language,
            "meta_title": self.meta_title,
            "meta_description": self.meta_description,
            "meta_keywords": self.meta_keywords,
            "word_count": self.word_count,
            "reading_time": self.reading_time,
            "primary_keyword": self.primary_keyword,
            "secondary_keywords": self.secondary_keywords,
            "keyword_density": self.keyword_density,
            "seo_score": self.seo_score,
            "readability_score": self.readability_score,
            "headings": self.headings,
            "images": self.images,
            "links": self.links,
            "ai_model": self.ai_model,
            "generation_settings": self.generation_settings,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "external_url": self.external_url,
            "suggestions": self.suggestions,
            "project_id": self.project_id,  # Already string
            "user_id": self.user_id,        # Already string
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        
        if include_content:
            data.update({
                "content": self.content,
                "html_content": self.html_content,
                "ai_prompt": self.ai_prompt,
            })
        
        if include_analytics:
            data.update({
                "views": self.views,
                "shares": self.shares,
                "engagement_score": self.engagement_score,
                "avg_ranking": self.avg_ranking,
                "search_impressions": self.search_impressions,
                "search_clicks": self.search_clicks,
                "ctr": self.ctr,
                "wordpress_id": self.wordpress_id,
            })
        
        return data
    
    @property
    def is_published(self) -> bool:
        """Check if article is published."""
        return self.status == ArticleStatus.PUBLISHED
    
    @property
    def is_scheduled(self) -> bool:
        """Check if article is scheduled for future publishing."""
        if not self.scheduled_at:
            return False
        return datetime.utcnow() < self.scheduled_at
    
    def calculate_reading_time(self) -> int:
        """Calculate estimated reading time based on word count."""
        if not self.word_count:
            return 0
        # Assuming average reading speed of 200 words per minute
        return max(1, self.word_count // 200)
    
    def update_word_count(self):
        """Update word count from content."""
        if self.content:
            # Simple word count (can be improved with better text processing)
            import re
            words = re.findall(r'\w+', self.content)
            self.word_count = len(words)
            self.reading_time = self.calculate_reading_time()
    
    def calculate_keyword_density(self) -> float:
        """Calculate keyword density for primary keyword."""
        if not self.content or not self.primary_keyword:
            return 0.0
        
        content_lower = self.content.lower()
        keyword_lower = self.primary_keyword.lower()
        
        # Count occurrences
        keyword_count = content_lower.count(keyword_lower)
        total_words = len(self.content.split())
        
        if total_words == 0:
            return 0.0
        
        density = (keyword_count / total_words) * 100
        self.keyword_density = round(density, 2)
        return self.keyword_density
    
    def extract_headings(self) -> List[Dict]:
        """Extract headings structure from content."""
        if not self.content:
            return []
        
        import re
        headings = []
        
        # Find H1-H6 tags in HTML content or markdown headers
        if self.html_content:
            pattern = r'<h([1-6]).*?>(.*?)</h[1-6]>'
            matches = re.findall(pattern, self.html_content, re.IGNORECASE | re.DOTALL)
            for level, text in matches:
                headings.append({
                    "level": int(level),
                    "text": re.sub(r'<.*?>', '', text).strip(),
                })
        else:
            # Markdown headers
            lines = self.content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('#'):
                    level = len(line) - len(line.lstrip('#'))
                    if level <= 6:
                        text = line.lstrip('#').strip()
                        headings.append({
                            "level": level,
                            "text": text,
                        })
        
        self.headings = headings
        return headings
    
    def add_suggestion(self, suggestion: str, category: str = "general"):
        """Add an improvement suggestion."""
        suggestion_obj = {
            "id": str(uuid4()),
            "category": category,
            "text": suggestion,
            "created_at": datetime.utcnow().isoformat(),
            "resolved": False,
        }
        
        if not isinstance(self.suggestions, list):
            self.suggestions = []
        
        self.suggestions.append(suggestion_obj)
    
    def mark_suggestion_resolved(self, suggestion_id: str):
        """Mark a suggestion as resolved."""
        for suggestion in self.suggestions:
            if suggestion.get("id") == suggestion_id:
                suggestion["resolved"] = True
                suggestion["resolved_at"] = datetime.utcnow().isoformat()
                break
    
    def publish(self):
        """Publish the article."""
        self.status = ArticleStatus.PUBLISHED
        self.published_at = datetime.utcnow()
    
    def unpublish(self):
        """Unpublish the article."""
        self.status = ArticleStatus.DRAFT
        self.published_at = None
    
    def schedule(self, scheduled_time: datetime):
        """Schedule the article for publishing."""
        self.scheduled_at = scheduled_time
        if scheduled_time > datetime.utcnow():
            self.status = ArticleStatus.REVIEW
    
    def get_seo_analysis(self) -> dict:
        """Get comprehensive SEO analysis."""
        analysis = {
            "overall_score": self.seo_score,
            "keyword_optimization": {
                "primary_keyword": self.primary_keyword,
                "keyword_density": self.keyword_density,
                "in_title": self.primary_keyword.lower() in self.title.lower() if self.primary_keyword else False,
                "in_meta_description": self.primary_keyword.lower() in (self.meta_description or "").lower() if self.primary_keyword else False,
            },
            "content_quality": {
                "word_count": self.word_count,
                "reading_time": self.reading_time,
                "readability_score": self.readability_score,
                "headings_count": len(self.headings),
            },
            "technical_seo": {
                "meta_title_length": len(self.meta_title) if self.meta_title else 0,
                "meta_description_length": len(self.meta_description) if self.meta_description else 0,
                "images_count": len(self.images),
                "internal_links": self.links.get("internal", []),
                "external_links": self.links.get("external", []),
            },
        }
        
        return analysis

# Add relationship to User and Project models
from app.models.user import User
from app.models.project import Project

User.articles = relationship("Article", back_populates="user")
Project.articles = relationship("Article", back_populates="project", cascade="all, delete-orphan")