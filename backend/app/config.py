"""
Configuration settings for SEO Article Writing System

This module handles all configuration settings including:
- Database connections
- API keys
- Redis settings
- Environment-specific configurations
"""

from pydantic import BaseSettings, Field
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # 基本應用設定
    app_name: str = "SEO Article Writing System"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # API 設定
    api_v1_prefix: str = "/api/v1"
    
    # 資料庫設定
    database_url: str = Field(..., env="DATABASE_URL")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Redis 設定
    redis_url: str = Field(..., env="REDIS_URL")
    redis_ttl: int = Field(default=604800, env="REDIS_TTL")  # 7 days
    
    # JWT 認證設定
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Google Custom Search API
    google_api_key: str = Field(..., env="GOOGLE_API_KEY")
    google_cx_id: str = Field(..., env="GOOGLE_CX_ID")
    google_daily_limit: int = Field(default=100, env="GOOGLE_DAILY_LIMIT")
    
    # OpenAI API 設定
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=4096, env="OPENAI_MAX_TOKENS")
    
    # 爬蟲設定
    crawler_delay: float = Field(default=1.0, env="CRAWLER_DELAY")  # 秒
    crawler_timeout: int = Field(default=30, env="CRAWLER_TIMEOUT")  # 秒
    crawler_max_concurrent: int = Field(default=10, env="CRAWLER_MAX_CONCURRENT")
    crawler_user_agent: str = Field(
        default="SEO-Article-Writing-System/1.0 (+https://github.com/Tab2005/SEO-Article-Writing-System)",
        env="CRAWLER_USER_AGENT"
    )
    
    # Celery 設定
    celery_broker_url: str = Field(..., env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(..., env="CELERY_RESULT_BACKEND")
    
    # 安全性設定
    allowed_hosts: list[str] = Field(default=["localhost", "127.0.0.1"], env="ALLOWED_HOSTS")
    cors_origins: list[str] = Field(default=["http://localhost:3000", "http://localhost:5173"], env="CORS_ORIGINS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# 建立全域設定實例
settings = Settings()

# 開發/測試時的預設值
if settings.debug:
    print(f"🚀 Loading {settings.app_name} v{settings.app_version} in DEBUG mode")
    print(f"📊 Database: {settings.database_url}")
    print(f"🔄 Redis: {settings.redis_url}")
    print(f"🌐 CORS Origins: {settings.cors_origins}")