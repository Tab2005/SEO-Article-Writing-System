"""
Configuration module for SEO Article Writing System.

Loads environment variables and provides typed settings.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "SEO Article Writing System"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/seo_article_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_expire_days: int = 7
    
    # Security
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    
    # Google Custom Search API
    google_api_key: Optional[str] = None
    google_cx_id: Optional[str] = None
    
    # Google OAuth
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    
    # OpenAI API
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period_hours: int = 1
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
