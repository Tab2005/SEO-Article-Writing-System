"""
Tests for QA Gate V1 API Endpoints and auditing service.
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
from app.models.article_brief import ArticleBrief
from app.models.article import Article, ArticleStatus

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
        description="這是一個用於測試 QA 的專案",
        target_market="tw",
        mode="existing_site",
        status="active"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    yield project


@pytest.fixture(name="mock_site_profile")
async def mock_site_profile_fixture(db_session: AsyncSession, mock_project: Project):
    """Fixture to create a mock site profile."""
    profile = SiteProfile(
        id=uuid.uuid4(),
        project_id=mock_project.id,
        site_name="SEO 專家網",
        business_type="blog",
        site_description="分享最新 SEO 行銷資訊的部落格",
        target_audiences=["數位行銷人", "中小企業主"],
        products_or_services=["SEO 教學課", "顧問諮詢"],
        core_topics=["搜尋引擎優化", "內容行銷", "關鍵字研究"],
        allowed_angles=["技術 SEO 教學", "長尾關鍵字規劃", "實用工具評測"],
        restricted_angles=["黑帽 SEO手法", "刷流量軟體推薦", "違法SEO手段"],
        summary_snapshot="SEO 專家網專門分享實用白帽 SEO 行銷技巧，禁止推廣黑帽或違規手法。",
        status="approved"
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    yield profile


@pytest.fixture(name="mock_brief")
async def mock_brief_fixture(db_session: AsyncSession, mock_project: Project):
    """Fixture to create a mock approved brief."""
    brief = ArticleBrief(
        id=uuid.uuid4(),
        project_id=mock_project.id,
        title_direction="2026 年最新 SEO 實用指南",
        article_role="pillar",
        search_intent="informational",
        target_audience="行銷經理、網站站長",
        primary_question="SEO 要怎麼做才能排上第一頁？",
        next_question="如何衡量 SEO 的投資報酬率？",
        info_gain_requirement="需要融入 ChatGPT 與生成式 AI 對 SEO 的影響分析",
        restricted_content="不要提及過時的黑帽 SEO 手法，不要推薦刷快排軟體",
        cta_direction="註冊免費 SEO 健檢服務",
        status="approved"
    )
    db_session.add(brief)
    await db_session.commit()
    await db_session.refresh(brief)
    yield brief


@pytest.fixture(name="mock_draft")
async def mock_draft_fixture(
    db_session: AsyncSession, 
    mock_project: Project, 
    mock_brief: ArticleBrief
):
    """Fixture to create a mock draft."""
    article = Article(
        id=uuid.uuid4(),
        project_id=mock_project.id,
        brief_id=mock_brief.id,
        title="2026 年最新 SEO 實用指南",
        content="""# 2026 年最新 SEO 實用指南

在 2026 年，搜尋引擎優化 (SEO) 經歷了巨大變革，尤其是生成式 AI (如 ChatGPT) 的普及。
為了在搜尋結果中排上第一頁，我們必須專注於提供實用價值與資訊增益。
不要使用任何刷點擊或黑帽 SEO 手法，那只會導致網站被 Google 懲罰。
如果有需要，歡迎註冊我們的免費 SEO 健檢服務。""",
        target_keyword="SEO 指南",
        word_count=500,
        status=ArticleStatus.DRAFT,
        qa_status="pending"
    )
    db_session.add(article)
    await db_session.commit()
    await db_session.refresh(article)
    yield article


@pytest.mark.asyncio
async def test_run_qa_success(
    client: AsyncClient, 
    mock_draft: Article, 
    mock_site_profile: SiteProfile
):
    """Test running QA Gate check successfully on an existing draft."""
    draft_id = str(mock_draft.id)
    response = await client.post(f"/api/v1/content/draft/{draft_id}/qa")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == draft_id
    assert data["qa_status"] in ["passed", "failed"]
    assert "qa_results" in data
    
    qa_results = data["qa_results"]
    assert "is_passed" in qa_results
    assert "issues" in qa_results
    
    # In mock mode, we expect is_passed to be True and some info_gain issues
    assert qa_results["is_passed"] is True
    assert len(qa_results["issues"]) > 0
    assert qa_results["issues"][0]["check_type"] == "info_gain"


@pytest.mark.asyncio
async def test_run_qa_not_found(client: AsyncClient, mock_site_profile: SiteProfile):
    """Test running QA check when draft ID does not exist."""
    fake_id = str(uuid.uuid4())
    response = await client.post(f"/api/v1/content/draft/{fake_id}/qa")
    assert response.status_code == 404
