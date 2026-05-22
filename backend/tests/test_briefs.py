"""
Tests for Article Brief API Endpoints.
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
from app.models.site_profile import SiteProfile
from app.models.qualification_result import QualificationResult
from app.models.article_brief import ArticleBrief

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
        description="這是一個用於測試 Brief 的專案",
        target_market="tw",
        mode="existing_site",
        status="active"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    yield project


@pytest.mark.asyncio
async def test_create_brief_manually(client: AsyncClient, mock_project: Project):
    """Test creating an article brief manually."""
    project_id = str(mock_project.id)
    payload = {
        "title_direction": "2026 年最新 SEO 實用指南",
        "article_role": "pillar",
        "search_intent": "informational",
        "target_audience": "行銷經理、網站站長",
        "primary_question": "SEO 要怎麼做才能排上第一頁？",
        "next_question": "如何衡量 SEO 的投資報酬率？",
        "info_gain_requirement": "需要融入 ChatGPT 與生成式 AI 對 SEO 的影響分析",
        "restricted_content": "不要提及過時的黑帽 SEO 手法",
        "recommended_internal_links": "內部連結至 /pillar-seo 頁面",
        "cta_direction": "註冊免費 SEO 健檢服務",
        "status": "draft"
    }
    
    response = await client.post(f"/api/v1/projects/{project_id}/briefs", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["title_direction"] == payload["title_direction"]
    assert data["article_role"] == payload["article_role"]
    assert data["status"] == "draft"
    assert "id" in data
    assert data["project_id"] == project_id


@pytest.mark.asyncio
async def test_list_briefs(client: AsyncClient, db_session: AsyncSession, mock_project: Project):
    """Test listing all briefs in a project."""
    project_id = mock_project.id
    
    # Pre-populate two briefs
    brief1 = ArticleBrief(
        id=uuid.uuid4(),
        project_id=project_id,
        title_direction="測試文章 1",
        status="draft"
    )
    brief2 = ArticleBrief(
        id=uuid.uuid4(),
        project_id=project_id,
        title_direction="測試文章 2",
        status="approved"
    )
    db_session.add_all([brief1, brief2])
    await db_session.commit()
    
    response = await client.get(f"/api/v1/projects/{str(project_id)}/briefs")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 2
    titles = [b["title_direction"] for b in data]
    assert "測試文章 1" in titles
    assert "測試文章 2" in titles


@pytest.mark.asyncio
async def test_get_single_brief(client: AsyncClient, db_session: AsyncSession, mock_project: Project):
    """Test retrieving a single article brief."""
    project_id = mock_project.id
    brief_id = uuid.uuid4()
    
    brief = ArticleBrief(
        id=brief_id,
        project_id=project_id,
        title_direction="獨家 SEO 指南",
        status="draft",
        target_audience="產品經理"
    )
    db_session.add(brief)
    await db_session.commit()
    
    response = await client.get(f"/api/v1/projects/{str(project_id)}/briefs/{str(brief_id)}")
    assert response.status_code == 200
    data = response.json()
    assert data["title_direction"] == "獨家 SEO 指南"
    assert data["target_audience"] == "產品經理"


@pytest.mark.asyncio
async def test_update_brief(client: AsyncClient, db_session: AsyncSession, mock_project: Project):
    """Test updating an existing article brief."""
    project_id = mock_project.id
    brief_id = uuid.uuid4()
    
    brief = ArticleBrief(
        id=brief_id,
        project_id=project_id,
        title_direction="舊文章方向",
        status="draft"
    )
    db_session.add(brief)
    await db_session.commit()
    
    payload = {
        "title_direction": "更新後的文章方向",
        "status": "approved",
        "target_audience": "行銷人員"
    }
    
    response = await client.patch(
        f"/api/v1/projects/{str(project_id)}/briefs/{str(brief_id)}",
        json=payload
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["title_direction"] == "更新後的文章方向"
    assert data["status"] == "approved"
    assert data["target_audience"] == "行銷人員"


@pytest.mark.asyncio
async def test_delete_brief(client: AsyncClient, db_session: AsyncSession, mock_project: Project):
    """Test deleting an article brief."""
    project_id = mock_project.id
    brief_id = uuid.uuid4()
    
    brief = ArticleBrief(
        id=brief_id,
        project_id=project_id,
        title_direction="即將被刪除的文章",
        status="draft"
    )
    db_session.add(brief)
    await db_session.commit()
    
    # Delete
    response = await client.delete(f"/api/v1/projects/{str(project_id)}/briefs/{str(brief_id)}")
    assert response.status_code == 204
    
    # Try to get again, should be 404
    get_response = await client.get(f"/api/v1/projects/{str(project_id)}/briefs/{str(brief_id)}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_create_brief_from_qualification(
    client: AsyncClient, db_session: AsyncSession, mock_project: Project
):
    """Test generating a structured article brief from a Qualified topic idea."""
    project_id = mock_project.id
    
    # 1. Create a SiteProfile for positioning constraints
    site_profile = SiteProfile(
        id=uuid.uuid4(),
        project_id=project_id,
        site_name="測試網站",
        business_type="SaaS 軟體服務",
        target_audiences=["軟體開發者", "專案經理"],
        restricted_angles=["黑帽 SEO 手法", "代寫服務"],
        primary_goals=["註冊免費試用", "預約 Demo"],
        status="approved"
    )
    
    # 2. Create a QualificationResult
    qualification_id = uuid.uuid4()
    qual_res = QualificationResult(
        id=qualification_id,
        project_id=project_id,
        input_term="如何選擇專案管理工具",
        decision="qualified",
        suggested_angle="從軟體開發者與專案經理的角度出發，對比不同工具的協同效率與整合能力。",
        target_journey_stage="consideration",
        review_status="approved"
    )
    
    db_session.add_all([site_profile, qual_res])
    await db_session.commit()
    
    # Trigger brief generation
    url = f"/api/v1/projects/{str(project_id)}/briefs/from-qualification/{str(qualification_id)}"
    response = await client.post(url)
    assert response.status_code == 201
    
    data = response.json()
    assert data["title_direction"] == "如何選擇專案管理工具"
    assert data["search_intent"] == "consideration"
    # Verify values mapped from SiteProfile
    assert "軟體開發者, 專案經理" in data["target_audience"]
    assert "黑帽 SEO 手法, 代寫服務" in data["restricted_content"]
    assert "註冊免費試用, 預約 Demo" in data["cta_direction"]
    # Verify values mapped from QualificationResult
    assert data["info_gain_requirement"] == "從軟體開發者與專案經理的角度出發，對比不同工具的協同效率與整合能力。"
