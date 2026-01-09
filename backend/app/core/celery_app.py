"""
Celery Application Configuration.

Sets up Celery for background task processing.
"""

from celery import Celery

from app.config import settings

# Create Celery app
celery_app = Celery(
    "seo_article_writer",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.research_tasks", "app.tasks.content_tasks"],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Taipei",
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    
    # Task routing (optional - for scaling)
    task_routes={
        "app.tasks.research_tasks.*": {"queue": "research"},
        "app.tasks.content_tasks.*": {"queue": "content"},
    },
    
    # Rate limiting
    task_default_rate_limit="10/m",
)
