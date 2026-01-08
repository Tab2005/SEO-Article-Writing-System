"""
Database Models Test Script

This script tests the database models and basic CRUD operations.
"""

import asyncio
import uuid
from datetime import datetime

from app.database import get_db, init_db, get_db_info, drop_db
from app.models import User, Project, Article, SearchCache, ProjectStatus, ArticleStatus

async def test_database_models():
    """Test all database models with basic operations."""
    print("🧪 Testing Database Models...")
    
    # Clean slate - drop and recreate tables
    print("🔄 Recreating database tables...")
    await drop_db()
    await init_db()
    print("✅ Database tables recreated")
    
    # Get database info
    db_info = await get_db_info()
    print(f"📊 Database Info: {db_info}")
    
    # Generate unique test data
    test_uuid = str(uuid.uuid4())[:8]
    
    # Test database session
    async for db in get_db():
        try:
            # Test User model
            print("\n👤 Testing User model...")
            test_user = User(
                username=f"testuser_{test_uuid}",
                email=f"test_{test_uuid}@example.com",
                hashed_password="fake_hashed_password",
                full_name="Test User"
            )
            db.add(test_user)
            await db.commit()
            await db.refresh(test_user)
            print(f"✅ User created: {test_user.username} (ID: {test_user.id})")
            
            # Test Project model
            print("\n📂 Testing Project model...")
            test_project = Project(
                name="Test SEO Project",
                description="A test project for SEO articles",
                user_id=test_user.id,
                primary_keywords=["SEO", "content", "marketing"],
                status=ProjectStatus.ACTIVE
            )
            db.add(test_project)
            await db.commit()
            await db.refresh(test_project)
            print(f"✅ Project created: {test_project.name} (ID: {test_project.id})")
            
            # Test Article model
            print("\n📝 Testing Article model...")
            test_article = Article(
                title="Test SEO Article",
                slug="test-seo-article",
                content="This is a test article about SEO best practices...",
                primary_keyword="SEO",
                status=ArticleStatus.DRAFT,
                project_id=test_project.id,
                user_id=test_user.id
            )
            test_article.update_word_count()
            db.add(test_article)
            await db.commit()
            await db.refresh(test_article)
            print(f"✅ Article created: {test_article.title} (ID: {test_article.id})")
            print(f"   Word count: {test_article.word_count}, Reading time: {test_article.reading_time} min")
            
            # Test SearchCache model
            print("\n🔍 Testing SearchCache model...")
            test_cache = SearchCache.create_cache_entry(
                query="SEO best practices",
                results={"items": [{"title": "Test Result", "link": "https://example.com"}]},
                user_id=test_user.id,
                project_id=test_project.id
            )
            db.add(test_cache)
            await db.commit()
            await db.refresh(test_cache)
            print(f"✅ Search cache created: {test_cache.query} (ID: {test_cache.id})")
            
            # Test model methods
            print("\n🔬 Testing model methods...")
            
            # User methods
            print(f"   User can make API call: {test_user.can_make_api_call()}")
            test_user.increment_api_calls()
            print(f"   API calls after increment: {test_user.api_calls_today}")
            
            # Project methods
            test_project.add_keyword("digital marketing")
            test_project.update_activity()
            print(f"   Project keywords: {test_project.get_all_keywords()}")
            
            # Article methods
            test_article.calculate_keyword_density()
            test_article.extract_headings()
            test_article.add_suggestion("Add more internal links", "seo")
            print(f"   Keyword density: {test_article.keyword_density}%")
            print(f"   Suggestions count: {len(test_article.suggestions)}")
            
            # Search cache methods
            test_cache.increment_hit_count()
            analysis = test_cache.perform_analysis()
            print(f"   Cache hits: {test_cache.hit_count}")
            print(f"   Analysis completed: {test_cache.analyzed}")
            
            # Test model relationships (avoid lazy loading)
            print("\n🔗 Testing relationships...")
            
            # Count relationships using queries instead of accessing lazy loaded attributes
            from sqlalchemy import select
            
            # Count user's projects
            user_projects_result = await db.execute(select(Project).where(Project.user_id == test_user.id))
            user_projects_count = len(user_projects_result.scalars().all())
            print(f"   User projects count: {user_projects_count}")
            
            # Count project's articles  
            project_articles_result = await db.execute(select(Article).where(Article.project_id == test_project.id))
            project_articles_count = len(project_articles_result.scalars().all())
            print(f"   Project articles count: {project_articles_count}")
            
            # Count user's search caches
            user_caches_result = await db.execute(select(SearchCache).where(SearchCache.user_id == test_user.id))
            user_caches_count = len(user_caches_result.scalars().all())
            print(f"   User search caches count: {user_caches_count}")
            
            # Test to_dict methods
            print("\n📄 Testing serialization...")
            user_dict = test_user.to_dict()
            project_dict = test_project.to_dict()
            article_dict = test_article.to_dict(include_content=False)
            cache_dict = test_cache.to_dict(include_results=False)
            
            print(f"   User dict keys: {list(user_dict.keys())}")
            print(f"   Project dict keys: {list(project_dict.keys())}")
            print(f"   Article dict keys: {list(article_dict.keys())}")
            print(f"   Cache dict keys: {list(cache_dict.keys())}")
            
            print("\n✅ All database models tested successfully!")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Test failed with error: {e}")
            raise e

if __name__ == "__main__":
    asyncio.run(test_database_models())