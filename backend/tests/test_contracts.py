"""
Contract tests for planning-to-content workflow rules.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.dependencies import get_current_user
from app.core.database import Base, get_db
from app.main import app
from app.models.article_brief import ArticleBrief
from app.models.project import Project
from app.models.site_profile import SiteProfile
from app.models.topic_node import TopicNode
from app.models.user import User


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def full_site_profile_payload() -> dict:
    """Return a site profile payload that satisfies the ready rule."""
    return {
        "site_name": "內容實驗室",
        "business_type": "SaaS 部落格",
        "site_description": "提供 SEO 與內容策略實作教學。",
        "target_audiences": ["內容經理", "行銷團隊"],
        "products_or_services": ["SEO 顧問服務"],
        "core_topics": ["SEO", "內容策略"],
        "allowed_angles": ["實戰拆解", "流程教學"],
        "restricted_angles": ["黑帽 SEO"],
        "brand_voice": "專業直接，避免空話。",
        "primary_goals": ["獲取潛在客戶"],
    }


@pytest.fixture(name="db_session")
async def db_session_fixture() -> AsyncSession:
    """Create database tables and provide a clean session for each test."""
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
    """Configure dependency overrides and return a test client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(name="mock_user")
async def mock_user_fixture(db_session: AsyncSession):
    """Create an authenticated user for the tests."""
    user = User(
        id=uuid.uuid4(),
        email="contract_user@example.com",
        hashed_password="hashedpassword123",
        full_name="契約測試使用者",
        is_active=True,
        is_verified=True,
        is_superuser=False,
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
    """Create a draft project owned by the authenticated user."""
    project = Project(
        id=uuid.uuid4(),
        owner_id=mock_user.id,
        name="契約測試專案",
        description="用於驗證 planning contract",
        target_market="tw",
        mode="existing_site",
        status="draft",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    yield project


@pytest.mark.asyncio
async def test_site_profile_stays_draft_until_all_ready_fields_are_complete(
    client: AsyncClient,
    mock_project: Project,
):
    """Site Profile should not become ready with only the three basic text fields."""
    response = await client.put(
        f"/api/v1/projects/{mock_project.id}/site-profile",
        json={
            "site_name": "內容實驗室",
            "business_type": "SaaS 部落格",
            "site_description": "只填三個欄位還不夠。",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_site_profile_becomes_ready_when_required_fields_are_complete(
    client: AsyncClient,
    mock_project: Project,
):
    """Site Profile should become ready once the canonical required fields are present."""
    response = await client.put(
        f"/api/v1/projects/{mock_project.id}/site-profile",
        json=full_site_profile_payload(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


@pytest.mark.asyncio
async def test_activate_project_recomputes_incomplete_site_profile_status(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_project: Project,
):
    """Activation should fail when a stale ready profile no longer meets the ready rule."""
    profile = SiteProfile(
        id=uuid.uuid4(),
        project_id=mock_project.id,
        site_name="內容實驗室",
        business_type="SaaS 部落格",
        site_description="舊資料只有三個文字欄位。",
        status="ready",
    )
    active_node = TopicNode(
        id=uuid.uuid4(),
        project_id=mock_project.id,
        name="SEO 基礎",
        topic_role="pillar",
        journey_stage="awareness",
        priority="high",
        status="active",
    )
    db_session.add_all([profile, active_node])
    await db_session.commit()

    response = await client.post(f"/api/v1/projects/{mock_project.id}/activate")

    assert response.status_code == 400
    assert "Site Profile is incomplete" in response.json()["detail"]

    await db_session.refresh(profile)
    assert profile.status == "draft"


@pytest.mark.asyncio
async def test_qualification_requires_active_project(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_project: Project,
):
    """Qualification should reject draft projects."""
    profile = SiteProfile(
        id=uuid.uuid4(),
        project_id=mock_project.id,
        status="ready",
        **full_site_profile_payload(),
    )
    active_node = TopicNode(
        id=uuid.uuid4(),
        project_id=mock_project.id,
        name="SEO 基礎",
        topic_role="pillar",
        journey_stage="awareness",
        priority="high",
        status="active",
    )
    db_session.add_all([profile, active_node])
    await db_session.commit()

    response = await client.post(
        f"/api/v1/projects/{mock_project.id}/qualification-results",
        json={"input_term": "AI SEO 寫作流程"},
    )

    assert response.status_code == 400
    assert "Project must be active" in response.json()["detail"]


@pytest.mark.asyncio
async def test_qualification_rejects_incomplete_site_profile_even_if_marked_ready(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_project: Project,
):
    """Qualification should not trust stale ready statuses."""
    mock_project.status = "active"
    profile = SiteProfile(
        id=uuid.uuid4(),
        project_id=mock_project.id,
        site_name="內容實驗室",
        business_type="SaaS 部落格",
        site_description="舊資料只有三個文字欄位。",
        status="ready",
    )
    active_node = TopicNode(
        id=uuid.uuid4(),
        project_id=mock_project.id,
        name="SEO 基礎",
        topic_role="pillar",
        journey_stage="awareness",
        priority="high",
        status="active",
    )
    await db_session.commit()
    db_session.add_all([profile, active_node])
    await db_session.commit()

    response = await client.post(
        f"/api/v1/projects/{mock_project.id}/qualification-results",
        json={"input_term": "AI SEO 寫作流程"},
    )

    assert response.status_code == 400
    assert "Site Profile must be ready" in response.json()["detail"]

    await db_session.refresh(profile)
    assert profile.status == "draft"


@pytest.mark.asyncio
async def test_qualification_requires_at_least_one_active_topic_node(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_project: Project,
):
    """Qualification should require at least one active topic node."""
    mock_project.status = "active"
    profile = SiteProfile(
        id=uuid.uuid4(),
        project_id=mock_project.id,
        status="ready",
        **full_site_profile_payload(),
    )
    inactive_node = TopicNode(
        id=uuid.uuid4(),
        project_id=mock_project.id,
        name="SEO 基礎",
        topic_role="pillar",
        journey_stage="awareness",
        priority="high",
        status="draft",
    )
    db_session.add_all([profile, inactive_node])
    await db_session.commit()

    response = await client.post(
        f"/api/v1/projects/{mock_project.id}/qualification-results",
        json={"input_term": "AI SEO 寫作流程"},
    )

    assert response.status_code == 400
    assert "active Topic Node" in response.json()["detail"]


@pytest.mark.asyncio
async def test_qualification_succeeds_when_project_profile_and_topic_map_are_ready(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_project: Project,
):
    """Qualification should run once all planning gates are satisfied."""
    mock_project.status = "active"
    profile = SiteProfile(
        id=uuid.uuid4(),
        project_id=mock_project.id,
        status="ready",
        **full_site_profile_payload(),
    )
    active_node = TopicNode(
        id=uuid.uuid4(),
        project_id=mock_project.id,
        name="SEO 基礎",
        topic_role="pillar",
        journey_stage="awareness",
        priority="high",
        status="active",
    )
    db_session.add_all([profile, active_node])
    await db_session.commit()

    response = await client.post(
        f"/api/v1/projects/{mock_project.id}/qualification-results",
        json={"input_term": "AI SEO 寫作流程"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["input_term"] == "AI SEO 寫作流程"
    assert data["decision"] == "qualified"


@pytest.mark.asyncio
async def test_generate_outline_rejects_unapproved_brief(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_project: Project,
):
    """Outline generation should only accept approved briefs."""
    draft_brief = ArticleBrief(
        id=uuid.uuid4(),
        project_id=mock_project.id,
        title_direction="未核准的文章方向",
        status="draft",
    )
    db_session.add(draft_brief)
    await db_session.commit()

    response = await client.post(
        "/api/v1/content/outline",
        json={
            "topic": "未核准的文章方向",
            "target_keyword": "未核准的文章方向",
            "secondary_keywords": [],
            "word_count_target": 2000,
            "tone": "professional",
            "market": "tw",
            "use_competitor_analysis": False,
            "brief_id": str(draft_brief.id),
        },
    )

    assert response.status_code == 400
    assert "has not been approved" in response.json()["detail"]


@pytest.mark.asyncio
async def test_generate_content_requires_brief_id(client: AsyncClient):
    """Content generation should reject requests that skip the brief layer."""
    response = await client.post(
        "/api/v1/content/generate",
        json={
            "topic": "直接生成的文章",
            "target_keyword": "直接生成的文章",
            "secondary_keywords": [],
            "word_count_target": 2000,
            "tone": "professional",
            "market": "tw",
        },
    )

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(error["loc"][-1] == "brief_id" for error in errors)
