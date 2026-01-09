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
]
