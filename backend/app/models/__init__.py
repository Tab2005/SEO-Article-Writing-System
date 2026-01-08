"""
Database models for the SEO Article Writing System.

This module exports all database models and provides
a centralized import point for SQLAlchemy models.
"""

# Import Base first
from app.database import Base

# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .project import Project, ProjectStatus
from .article import Article, ArticleStatus, ArticleType
from .search_cache import SearchCache

# Export all models
__all__ = [
    "Base",
    "User",
    "Project",
    "ProjectStatus", 
    "Article",
    "ArticleStatus",
    "ArticleType",
    "SearchCache",
]