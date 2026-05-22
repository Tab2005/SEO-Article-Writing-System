"""
Tests for Project Content Queue Endpoints.
"""

import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.core.database import get_db, Base
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.article import Article, ArticleStatus
from app.models.article_brief import ArticleBrief
from app.models.qualification_result import QualificationResult
from app.models.topic_node import TopicNode

# In-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(name="db_session")
async def db_session_fixture() -> AsyncSession:
    """Fixture to create database tables and provide a session for each test."""
    engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_maker() as session:
        yield session
        
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        
    await engine.dispose()


@pytest.fixture(name="client")
async def client_fixture(db_session: AsyncSession):
    """Fixture to configure application dependencies overrides and return test client."""
    async def override_get_db():
        yield db_session
        
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
        
    app.dependency_overrides.clear()


@pytest.fixture(name="mock_user")
async def mock_user_fixture(db_session: AsyncSession):
    """Fixture to create a test user and override auth dependency."""
    user = User(
        id=uuid.uuid4(),
        email="test_user@example.com",
        hashed_password="hashedpassword123",
        full_name="測試使用者",
        is_active=True,
        is_verified=True,
        is_superuser=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    async def override_get_current_user():
        return user
        
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield user


@pytest.fixture(name="mock_project")
async def mock_project_fixture(db_session: AsyncSession, mock_user: User):
    """Fixture to create a test project owned by the mock user."""
    project = Project(
        id=uuid.uuid4(),
        owner_id=mock_user.id,
        name="測試專案",
        description="這是一個用於測試 Content Queue 的專案",
        target_market="tw",
        mode="existing_site",
        status="active"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    yield project


@pytest.mark.asyncio
async def test_get_content_queue_empty(client: AsyncClient, mock_project: Project):
    """Test getting content queue when it is empty."""
    project_id = str(mock_project.id)
    response = await client.get(f"/api/v1/projects/{project_id}/content-queue")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_content_queue_aggregated(client: AsyncClient, db_session: AsyncSession, mock_project: Project):
    """Test getting content queue with various aggregated items (qualified, brief_draft, brief_approved, draft_writing)."""
    project_id = mock_project.id
    
    # 1. Qualified unlinked topic
    qual = QualificationResult(
        id=uuid.uuid4(),
        project_id=project_id,
        input_term="SEO 教學",
        decision="qualified",
        target_journey_stage="awareness"
    )
    
    # 2. Brief Draft
    brief1 = ArticleBrief(
        id=uuid.uuid4(),
        project_id=project_id,
        title_direction="AI 寫作工具評測",
        status="draft"
    )
    
    # 3. Brief Approved
    brief2 = ArticleBrief(
        id=uuid.uuid4(),
        project_id=project_id,
        title_direction="內容行銷策略",
        status="approved"
    )
    
    # 4. Draft Writing (Brief + Article Draft)
    brief3 = ArticleBrief(
        id=uuid.uuid4(),
        project_id=project_id,
        title_direction="SEO 關鍵字規劃",
        status="approved"
    )
    
    db_session.add_all([qual, brief1, brief2, brief3])
    await db_session.commit()
    
    # Add Article Draft for brief3
    article = Article(
        id=uuid.uuid4(),
        project_id=project_id,
        brief_id=brief3.id,
        title="SEO 關鍵字規劃實戰",
        target_keyword="SEO 關鍵字規劃",
        content="這是測試文章內容",
        word_count=10,
        status=ArticleStatus.DRAFT,
        qa_status="idle"
    )
    db_session.add(article)
    await db_session.commit()
    
    response = await client.get(f"/api/v1/projects/{str(project_id)}/content-queue")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    
    # Check states
    status_map = {item["keyword"]: item["status"] for item in data}
    assert status_map["SEO 教學"] == "qualified"
    assert status_map["AI 寫作工具評測"] == "brief_draft"
    assert status_map["內容行銷策略"] == "brief_approved"
    assert status_map["SEO 關鍵字規劃"] == "draft_writing"
