"""
Search cache model for storing Google Search API results.

This model handles:
- Caching Google Search API results
- Keyword research data
- Search volume and competition metrics
- SERP analysis and competitor data
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Float, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import hashlib

from app.database import Base

class SearchCache(Base):
    """Search cache model for storing Google Search API results."""
    
    __tablename__ = "search_caches"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()), index=True)
    
    # Search parameters
    query = Column(String(500), nullable=False, index=True)
    language = Column(String(10), default="zh-TW", nullable=False)
    country = Column(String(5), default="TW", nullable=False)
    location = Column(String(100), nullable=True)
    
    # Search type and parameters
    search_type = Column(String(50), nullable=False, index=True)  # 'web', 'image', 'news', 'shopping'
    num_results = Column(Integer, default=10, nullable=False)
    
    # Cache identification (for deduplication)
    cache_key = Column(String(64), nullable=False, unique=True, index=True)  # MD5 hash of search params
    
    # Search results data
    results = Column(JSON, nullable=False)  # Raw search results
    total_results = Column(Integer, default=0, nullable=False)
    search_time = Column(Float, default=0.0, nullable=False)  # API response time in seconds
    
    # SERP analysis data
    serp_features = Column(JSON, default=dict, nullable=False)  # Featured snippets, ads, etc.
    organic_results = Column(JSON, default=list, nullable=False)  # Cleaned organic results
    
    # Keyword metrics (if available)
    search_volume = Column(Integer, nullable=True)  # Monthly search volume
    competition_level = Column(String(20), nullable=True)  # LOW, MEDIUM, HIGH
    competition_index = Column(Float, nullable=True)  # 0.0 to 1.0
    cpc_low = Column(Float, nullable=True)  # Cost per click low range
    cpc_high = Column(Float, nullable=True)  # Cost per click high range
    
    # Analysis metadata
    analyzed = Column(Boolean, default=False, nullable=False)
    analysis_data = Column(JSON, default=dict, nullable=False)  # Processed analysis results
    
    # Cache management
    hit_count = Column(Integer, default=1, nullable=False)  # Number of cache hits
    last_accessed = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Foreign keys
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="search_caches")
    user = relationship("User", back_populates="search_caches")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_search_cache_query_lang_country', 'query', 'language', 'country'),
        Index('idx_search_cache_expires', 'expires_at'),
        Index('idx_search_cache_user_project', 'user_id', 'project_id'),
    )
    
    def __repr__(self):
        return f"<SearchCache(id={self.id}, query='{self.query[:50]}...', type='{self.search_type}')>"
    
    @classmethod
    def generate_cache_key(cls, query: str, language: str = "zh-TW", country: str = "TW", 
                          search_type: str = "web", num_results: int = 10) -> str:
        """Generate cache key for search parameters."""
        params = f"{query}|{language}|{country}|{search_type}|{num_results}"
        return hashlib.md5(params.encode('utf-8')).hexdigest()
    
    @classmethod
    def create_cache_entry(cls, query: str, results: dict, user_id: str, 
                          project_id: Optional[str] = None, language: str = "zh-TW", 
                          country: str = "TW", search_type: str = "web", 
                          num_results: int = 10, cache_hours: int = 24) -> 'SearchCache':
        """Create a new cache entry."""
        cache_key = cls.generate_cache_key(query, language, country, search_type, num_results)
        expires_at = datetime.utcnow() + timedelta(hours=cache_hours)
        
        return cls(
            query=query,
            language=language,
            country=country,
            search_type=search_type,
            num_results=num_results,
            cache_key=cache_key,
            results=results,
            total_results=results.get('searchInformation', {}).get('totalResults', 0),
            expires_at=expires_at,
            user_id=user_id,
            project_id=project_id,
        )
    
    def to_dict(self, include_results: bool = True) -> dict:
        """Convert search cache to dictionary."""
        data = {
            "id": self.id,  # Already string
            "query": self.query,
            "language": self.language,
            "country": self.country,
            "location": self.location,
            "search_type": self.search_type,
            "num_results": self.num_results,
            "cache_key": self.cache_key,
            "total_results": self.total_results,
            "search_time": self.search_time,
            "serp_features": self.serp_features,
            "organic_results": self.organic_results,
            "search_volume": self.search_volume,
            "competition_level": self.competition_level,
            "competition_index": self.competition_index,
            "cpc_low": self.cpc_low,
            "cpc_high": self.cpc_high,
            "analyzed": self.analyzed,
            "analysis_data": self.analysis_data,
            "hit_count": self.hit_count,
            "last_accessed": self.last_accessed.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "project_id": self.project_id,  # Already string or None
            "user_id": self.user_id,        # Already string
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        
        if include_results:
            data["results"] = self.results
        
        return data
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_fresh(self) -> bool:
        """Check if cache is fresh (not expired)."""
        return not self.is_expired
    
    def increment_hit_count(self):
        """Increment cache hit count and update last accessed time."""
        self.hit_count += 1
        self.last_accessed = datetime.utcnow()
    
    def extend_expiry(self, hours: int = 24):
        """Extend cache expiry time."""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
    
    def extract_organic_results(self) -> List[dict]:
        """Extract and clean organic search results."""
        organic = []
        
        if 'items' in self.results:
            for item in self.results['items']:
                organic_item = {
                    "title": item.get('title', ''),
                    "link": item.get('link', ''),
                    "snippet": item.get('snippet', ''),
                    "displayLink": item.get('displayLink', ''),
                    "position": len(organic) + 1,
                }
                
                # Extract additional metadata if available
                if 'pagemap' in item:
                    organic_item['pagemap'] = item['pagemap']
                
                organic.append(organic_item)
        
        self.organic_results = organic
        return organic
    
    def analyze_serp_features(self) -> dict:
        """Analyze SERP features from search results."""
        features = {
            "featured_snippet": False,
            "people_also_ask": False,
            "related_searches": False,
            "knowledge_panel": False,
            "ads_count": 0,
            "organic_count": 0,
        }
        
        if 'items' in self.results:
            features["organic_count"] = len(self.results['items'])
        
        # Check for featured snippets (this would need API-specific parsing)
        # This is a simplified version - actual implementation would depend on API response format
        
        self.serp_features = features
        return features
    
    def get_competitor_analysis(self) -> dict:
        """Get competitor analysis from organic results."""
        if not self.organic_results:
            self.extract_organic_results()
        
        competitors = []
        domains = set()
        
        for result in self.organic_results[:10]:  # Top 10 results
            link = result.get('link', '')
            display_link = result.get('displayLink', '')
            
            if display_link and display_link not in domains:
                domains.add(display_link)
                competitors.append({
                    "domain": display_link,
                    "title": result.get('title', ''),
                    "url": link,
                    "snippet": result.get('snippet', ''),
                    "position": result.get('position', 0),
                })
        
        analysis = {
            "total_competitors": len(competitors),
            "unique_domains": list(domains),
            "top_competitors": competitors[:5],
            "competition_strength": "HIGH" if len(competitors) >= 8 else "MEDIUM" if len(competitors) >= 5 else "LOW",
        }
        
        return analysis
    
    def update_keyword_metrics(self, volume: Optional[int] = None, 
                             competition: Optional[str] = None,
                             competition_index: Optional[float] = None,
                             cpc_low: Optional[float] = None,
                             cpc_high: Optional[float] = None):
        """Update keyword metrics data."""
        if volume is not None:
            self.search_volume = volume
        if competition is not None:
            self.competition_level = competition
        if competition_index is not None:
            self.competition_index = competition_index
        if cpc_low is not None:
            self.cpc_low = cpc_low
        if cpc_high is not None:
            self.cpc_high = cpc_high
    
    def perform_analysis(self):
        """Perform comprehensive analysis of search results."""
        if self.analyzed:
            return self.analysis_data
        
        analysis = {
            "organic_analysis": self.extract_organic_results(),
            "serp_features": self.analyze_serp_features(),
            "competitor_analysis": self.get_competitor_analysis(),
            "analyzed_at": datetime.utcnow().isoformat(),
        }
        
        self.analysis_data = analysis
        self.analyzed = True
        
        return analysis
    
    def get_keyword_difficulty(self) -> str:
        """Calculate keyword difficulty based on available metrics."""
        if self.competition_index is not None:
            if self.competition_index >= 0.8:
                return "VERY_HIGH"
            elif self.competition_index >= 0.6:
                return "HIGH"
            elif self.competition_index >= 0.4:
                return "MEDIUM"
            elif self.competition_index >= 0.2:
                return "LOW"
            else:
                return "VERY_LOW"
        
        # Fallback to competition level
        if self.competition_level:
            return self.competition_level
        
        return "UNKNOWN"

# Add relationships to User and Project models
from app.models.user import User
from app.models.project import Project

User.search_caches = relationship("SearchCache", back_populates="user")
Project.search_caches = relationship("SearchCache", back_populates="project", cascade="all, delete-orphan")