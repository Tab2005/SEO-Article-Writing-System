"""
Tests for Article Versioning and Rollback API Endpoints.
"""

import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from app.main import app
from app.core.database import get_db, Base
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.article import Article, ArticleStatus
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
        description="這是一個用於測試 Versioning 的專案",
        target_market="tw",
        mode="existing_site",
        status="active"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    yield project


@pytest.fixture(name="mock_brief")
async def mock_brief_fixture(db_session: AsyncSession, mock_project: Project):
    """Fixture to create an approved brief for article generation."""
    brief = ArticleBrief(
        id=uuid.uuid4(),
        project_id=mock_project.id,
        title_direction="測試文章主題",
        status="approved"
    )
    db_session.add(brief)
    await db_session.commit()
    await db_session.refresh(brief)
    yield brief


@pytest.mark.asyncio
async def test_save_draft_version(client: AsyncClient, db_session: AsyncSession, mock_project: Project):
    """Test manual saving of draft versions."""
    project_id = str(mock_project.id)
    
    # 1. Create a draft
    create_payload = {
        "project_id": project_id,
        "keyword": "測試關鍵字",
        "title": "初始文章標題",
        "wizard_step": 4,
        "content": "這是初始文章內容，版本一的文字。"
    }
    create_response = await client.post("/api/v1/content/draft", json=create_payload)
    assert create_response.status_code == 201
    draft_id = create_response.json()["id"]

    # Update draft content to simulate writing
    update_payload = {
        "content": "這是初始文章內容，版本一的文字。"
    }
    update_response = await client.patch(f"/api/v1/content/draft/{draft_id}", json=update_payload)
    assert update_response.status_code == 200

    # 2. Save version (V1)
    save_response = await client.post(f"/api/v1/content/draft/{draft_id}/save-version")
    assert save_response.status_code == 200
    data = save_response.json()
    assert data["message"] == "Draft version saved successfully"
    assert data["version"] == 1
    
    # Check that main draft version incremented to 2
    get_response = await client.get(f"/api/v1/content/draft/{draft_id}")
    assert get_response.status_code == 200
    
    # Verify DB has the backup record
    result = await db_session.execute(
        select(Article)
        .where(Article.parent_version_id == uuid.UUID(draft_id))
    )
    backups = result.scalars().all()
    assert len(backups) == 1
    assert backups[0].version == 1
    assert backups[0].content == "這是初始文章內容，版本一的文字。"


@pytest.mark.asyncio
async def test_list_draft_versions(client: AsyncClient, db_session: AsyncSession, mock_project: Project):
    """Test retrieving list of draft versions."""
    project_id = mock_project.id
    draft_id = uuid.uuid4()
    
    # Create draft directly in DB
    draft = Article(
        id=draft_id,
        project_id=project_id,
        title="主要文章標題",
        target_keyword="測試",
        content="目前最新內容",
        version=3,
        status=ArticleStatus.DRAFT
    )
    
    # Create 2 historical backups
    backup1 = Article(
        id=uuid.uuid4(),
        project_id=project_id,
        title="歷史版本 1 標題",
        target_keyword="測試",
        content="歷史版本 1 內容",
        version=1,
        parent_version_id=draft_id,
        status=ArticleStatus.DRAFT
    )
    backup2 = Article(
        id=uuid.uuid4(),
        project_id=project_id,
        title="歷史版本 2 標題",
        target_keyword="測試",
        content="歷史版本 2 內容",
        version=2,
        parent_version_id=draft_id,
        status=ArticleStatus.DRAFT
    )
    
    db_session.add_all([draft, backup1, backup2])
    await db_session.commit()
    
    # Call endpoint to list versions
    response = await client.get(f"/api/v1/content/draft/{str(draft_id)}/versions")
    assert response.status_code == 200
    versions = response.json()
    assert len(versions) == 2
    
    # Should be sorted by version descending (newest version first)
    assert versions[0]["version"] == 2
    assert versions[0]["title"] == "歷史版本 2 標題"
    assert versions[1]["version"] == 1
    assert versions[1]["title"] == "歷史版本 1 標題"


@pytest.mark.asyncio
async def test_rollback_draft_version(client: AsyncClient, db_session: AsyncSession, mock_project: Project):
    """Test rolling back to a historical version."""
    project_id = mock_project.id
    draft_id = uuid.uuid4()
    backup_id = uuid.uuid4()
    
    # Create draft directly in DB
    draft = Article(
        id=draft_id,
        project_id=project_id,
        title="最新的文章標題",
        target_keyword="測試",
        content="最新的文章內容",
        version=2,
        status=ArticleStatus.DRAFT
    )
    
    # Create historical backup
    backup = Article(
        id=backup_id,
        project_id=project_id,
        title="歷史版本 1 標題",
        target_keyword="測試",
        content="歷史版本 1 內容",
        version=1,
        parent_version_id=draft_id,
        status=ArticleStatus.DRAFT
    )
    
    db_session.add_all([draft, backup])
    await db_session.commit()
    
    # Rollback to historical version
    url = f"/api/v1/content/draft/{str(draft_id)}/versions/{str(backup_id)}/rollback"
    response = await client.post(url)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Draft rolled back successfully"
    assert data["content"] == "歷史版本 1 內容"
    assert data["title"] == "歷史版本 1 標題"
    
    # Refresh DB session to fetch updated state
    await db_session.refresh(draft)
    assert draft.content == "歷史版本 1 內容"
    assert draft.title == "歷史版本 1 標題"
    assert draft.version == 3  # Increment version on rollback because it performs a save_version of the current state before rolling back
    
    # Ensure a backup of the 'latest' pre-rollback state was created
    result = await db_session.execute(
        select(Article)
        .where(Article.parent_version_id == draft_id, Article.version == 2)
    )
    rollback_backup = result.scalar_one_or_none()
    assert rollback_backup is not None
    assert rollback_backup.content == "最新的文章內容"


@pytest.mark.asyncio
async def test_auto_backup_on_generate(client: AsyncClient, db_session: AsyncSession, mock_project: Project, mock_brief: ArticleBrief):
    """Test that regenerating content automatically backups the existing draft if it has content."""
    project_id = mock_project.id
    brief_id = mock_brief.id
    
    # Create draft associated with brief directly in DB, which already has content
    draft = Article(
        id=uuid.uuid4(),
        project_id=project_id,
        brief_id=brief_id,
        title="原本的文章標題",
        target_keyword="測試文章主題",
        content="原本的文章內容，這是一篇有內容的文章，因此應該被自動備份。",
        version=1,
        status=ArticleStatus.DRAFT
    )
    db_session.add(draft)
    await db_session.commit()
    
    # Regenerate content via /generate endpoint
    payload = {
        "topic": "測試文章主題",
        "target_keyword": "測試文章主題",
        "secondary_keywords": [],
        "word_count_target": 2000,
        "tone": "professional",
        "market": "tw",
        "brief_id": str(brief_id)
    }
    
    response = await client.post("/api/v1/content/generate", json=payload)
    assert response.status_code == 201
    
    # Check that a backup version was created for draft
    result = await db_session.execute(
        select(Article)
        .where(Article.parent_version_id == draft.id)
    )
    backups = result.scalars().all()
    assert len(backups) == 1
    assert backups[0].content == "原本的文章內容，這是一篇有內容的文章，因此應該被自動備份。"
    assert backups[0].version == 1
    
    # Check that main draft version incremented to 2
    await db_session.refresh(draft)
    assert draft.version == 2
