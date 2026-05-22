"""
Schemas Package.

Pydantic schemas for request/response validation.
"""

from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    PasswordChange,
    Token,
    TokenPayload,
)
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectWithArticles,
)
from app.schemas.article import (
    ArticleCreate,
    ArticleUpdate,
    ArticleResponse,
    ArticleGenerateRequest,
    ArticleOutline,
    OutlineSection,
)
from app.schemas.research import (
    KeywordResearchRequest,
    SerpResult,
    SerpResponse,
    CompetitorData,
    AnalysisReport,
    ResearchTaskStatus,
    ResearchTaskCreate,
)
from app.schemas.site_profile import (
    SiteProfileCreate,
    SiteProfileUpdate,
    SiteProfileResponse,
)
from app.schemas.topic_node import (
    TopicNodeCreate,
    TopicNodeUpdate,
    TopicNodeMove,
    TopicNodeResponse,
    TopicNodeTreeResponse,
)
from app.schemas.content_item import (
    ContentItemImportRequest,
    ContentItemUpdate,
    ContentItemResponse,
    ContentItemMapTopic,
)
from app.schemas.qualification import (
    QualificationRequest,
    QualificationUpdate,
    QualificationResponse,
)
from app.schemas.brief import (
    BriefCreate,
    BriefUpdate,
    BriefResponse,
)
from app.schemas.content_queue import (
    ContentQueueItemResponse,
)

__all__ = [
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "PasswordChange",
    "Token",
    "TokenPayload",
    # Project
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectWithArticles",
    # Article
    "ArticleCreate",
    "ArticleUpdate",
    "ArticleResponse",
    "ArticleGenerateRequest",
    "ArticleOutline",
    "OutlineSection",
    # Research
    "KeywordResearchRequest",
    "SerpResult",
    "SerpResponse",
    "CompetitorData",
    "AnalysisReport",
    "ResearchTaskStatus",
    "ResearchTaskCreate",
    # Site Profile
    "SiteProfileCreate",
    "SiteProfileUpdate",
    "SiteProfileResponse",
    # Topic Node
    "TopicNodeCreate",
    "TopicNodeUpdate",
    "TopicNodeMove",
    "TopicNodeResponse",
    "TopicNodeTreeResponse",
    # Content Item
    "ContentItemImportRequest",
    "ContentItemUpdate",
    "ContentItemResponse",
    "ContentItemMapTopic",
    # Qualification
    "QualificationRequest",
    "QualificationUpdate",
    "QualificationResponse",
    # Brief
    "BriefCreate",
    "BriefUpdate",
    "BriefResponse",
    # Content Queue
    "ContentQueueItemResponse",
]
