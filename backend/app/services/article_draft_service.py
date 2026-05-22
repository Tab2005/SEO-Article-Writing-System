"""
Article Draft Service.

Manages article draft CRUD operations for Strategy Wizard.
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.orm import selectinload

from app.models.article import Article, ArticleStatus
from app.core.database import get_db


class ArticleDraftService:
    """
    Service for managing article drafts.
    
    Handles create, update, get, and list operations for wizard drafts.
    """
    
    async def create_draft(
        self,
        db: AsyncSession,
        *,
        project_id: uuid.UUID,
        keyword: str,
        title: str = "",
        wizard_step: int = 1,
        strategy_config: Optional[Dict[str, Any]] = None,
        outline: Optional[Dict[str, Any]] = None,
        research_job_id: Optional[uuid.UUID] = None,
        brief_id: Optional[uuid.UUID] = None,
    ) -> Article:
        """
        Create a new article draft.
        
        Args:
            db: Database session
            project_id: Project to associate with
            keyword: Target keyword
            title: Article title (can be empty initially)
            wizard_step: Current wizard step (1-4)
            strategy_config: Strategy settings (intent, tone, lsi, etc.)
            outline: Article outline structure
            research_job_id: Associated research job
            brief_id: Associated article brief
            
        Returns:
            Created Article instance
        """
        draft = Article(
            project_id=project_id,
            title=title or f"Draft: {keyword}",
            target_keyword=keyword,
            status=ArticleStatus.DRAFT,
            wizard_step=wizard_step,
            strategy_config=strategy_config,
            outline=outline,
            research_job_id=research_job_id,
            brief_id=brief_id,
            qa_status="pending",
        )
        
        db.add(draft)
        await db.commit()
        await db.refresh(draft)
        
        return draft
    
    async def update_draft(
        self,
        db: AsyncSession,
        draft_id: uuid.UUID,
        *,
        title: Optional[str] = None,
        wizard_step: Optional[int] = None,
        strategy_config: Optional[Dict[str, Any]] = None,
        outline: Optional[Dict[str, Any]] = None,
        content: Optional[str] = None,
        status: Optional[ArticleStatus] = None,
        word_count: Optional[int] = None,
        secondary_keywords: Optional[List[str]] = None,
        brief_id: Optional[uuid.UUID] = None,
        qa_status: Optional[str] = None,
        qa_results: Optional[Dict[str, Any]] = None,
    ) -> Optional[Article]:
        """
        Update an existing draft.
        
        Only updates fields that are explicitly provided.
        
        Args:
            db: Database session
            draft_id: Draft ID to update
            ... other optional fields
            
        Returns:
            Updated Article or None if not found
        """
        # Build update dict with only provided values
        update_data: Dict[str, Any] = {}
        
        if title is not None:
            update_data["title"] = title
        if wizard_step is not None:
            update_data["wizard_step"] = wizard_step
        if strategy_config is not None:
            update_data["strategy_config"] = strategy_config
        if outline is not None:
            update_data["outline"] = outline
        if content is not None:
            update_data["content"] = content
        if status is not None:
            update_data["status"] = status
        if word_count is not None:
            update_data["word_count"] = word_count
        if secondary_keywords is not None:
            update_data["secondary_keywords"] = secondary_keywords
        if brief_id is not None:
            update_data["brief_id"] = brief_id
        if qa_status is not None:
            update_data["qa_status"] = qa_status
        if qa_results is not None:
            update_data["qa_results"] = qa_results
        
        if not update_data:
            # No updates, just return the draft
            return await self.get_draft(db, draft_id)
        
        # Perform update
        stmt = (
            update(Article)
            .where(Article.id == draft_id)
            .values(**update_data)
            .returning(Article)
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        updated = result.scalar_one_or_none()
        if updated:
            await db.refresh(updated)
        
        return updated
    
    async def get_draft(
        self,
        db: AsyncSession,
        draft_id: uuid.UUID,
    ) -> Optional[Article]:
        """
        Get a draft by ID.
        
        Args:
            db: Database session
            draft_id: Draft ID
            
        Returns:
            Article or None
        """
        result = await db.execute(
            select(Article)
            .where(Article.id == draft_id)
        )
        return result.scalar_one_or_none()
    
    async def list_drafts(
        self,
        db: AsyncSession,
        *,
        project_id: Optional[uuid.UUID] = None,
        status: Optional[ArticleStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Article]:
        """
        List drafts with optional filtering.
        
        Args:
            db: Database session
            project_id: Filter by project
            status: Filter by status
            limit: Max results
            offset: Pagination offset
            
        Returns:
            List of Articles
        """
        query = select(Article).order_by(desc(Article.updated_at))
        
        if project_id:
            query = query.where(Article.project_id == project_id)
        if status:
            query = query.where(Article.status == status)
        
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def delete_draft(
        self,
        db: AsyncSession,
        draft_id: uuid.UUID,
    ) -> bool:
        """
        Delete a draft.
        
        Args:
            db: Database session
            draft_id: Draft ID
            
        Returns:
            True if deleted, False if not found
        """
        draft = await self.get_draft(db, draft_id)
        if not draft:
            return False
        
        await db.delete(draft)
        await db.commit()
        return True
    
    async def save_wizard_progress(
        self,
        db: AsyncSession,
        draft_id: uuid.UUID,
        step: int,
        data: Dict[str, Any],
    ) -> Optional[Article]:
        """
        Save wizard progress at a specific step.
        
        Convenience method that updates the draft with step-specific data.
        
        Args:
            db: Database session
            draft_id: Draft ID
            step: Current wizard step (1-4)
            data: Step-specific data to save
            
        Returns:
            Updated Article or None
        """
        update_kwargs: Dict[str, Any] = {"wizard_step": step}
        
        if step == 1:
            # Step 1: Research completed
            update_kwargs["research_job_id"] = data.get("research_job_id")
            
        elif step == 2:
            # Step 2: Strategy selected
            update_kwargs["strategy_config"] = {
                "intent": data.get("intent"),
                "tone": data.get("tone"),
                "lsi_keywords": data.get("lsi_keywords"),
                "suggested_titles": data.get("suggested_titles"),
            }
            if data.get("title"):
                update_kwargs["title"] = data["title"]
            if data.get("secondary_keywords"):
                update_kwargs["secondary_keywords"] = data["secondary_keywords"]
                
        elif step == 3:
            # Step 3: Outline finalized
            update_kwargs["outline"] = data.get("outline")
            if data.get("title"):
                update_kwargs["title"] = data["title"]
                
        elif step == 4:
            # Step 4: Content generated
            update_kwargs["content"] = data.get("content")
            update_kwargs["word_count"] = data.get("word_count", 0)
            update_kwargs["status"] = ArticleStatus.REVIEW
        
        return await self.update_draft(db, draft_id, **update_kwargs)

    async def create_draft_version(
        self,
        db: AsyncSession,
        draft_id: uuid.UUID,
    ) -> Optional[Article]:
        """
        Create a backup version of the current draft.
        The backup will have parent_version_id pointing to the main draft.
        The main draft's version counter will increment.
        """
        draft = await self.get_draft(db, draft_id)
        if not draft or draft.parent_version_id is not None:
            return None
            
        # Create historical backup
        backup = Article(
            project_id=draft.project_id,
            brief_id=draft.brief_id,
            title=draft.title,
            slug=draft.slug,
            content=draft.content,
            outline=draft.outline,
            target_keyword=draft.target_keyword,
            secondary_keywords=draft.secondary_keywords,
            meta_description=draft.meta_description,
            strategy_config=draft.strategy_config,
            research_job_id=draft.research_job_id,
            wizard_step=draft.wizard_step,
            word_count=draft.word_count,
            status=draft.status,
            qa_status=draft.qa_status,
            qa_results=draft.qa_results,
            version=draft.version, # Matches the current main version
            parent_version_id=draft.id, # Points to main
        )
        db.add(backup)
        
        # Increment main draft's version
        draft.version += 1
        draft.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(backup)
        await db.refresh(draft)
        return backup

    async def list_draft_versions(
        self,
        db: AsyncSession,
        draft_id: uuid.UUID,
    ) -> List[Article]:
        """
        List all backup versions for a draft.
        """
        result = await db.execute(
            select(Article)
            .where(Article.parent_version_id == draft_id)
            .order_by(desc(Article.version))
        )
        return list(result.scalars().all())

    async def rollback_to_version(
        self,
        db: AsyncSession,
        draft_id: uuid.UUID,
        version_id: uuid.UUID,
    ) -> Optional[Article]:
        """
        Rollback the main draft to a historical version.
        Before rolling back, a backup of the current state is created.
        """
        draft = await self.get_draft(db, draft_id)
        if not draft or draft.parent_version_id is not None:
            return None
            
        # Get target version
        result = await db.execute(
            select(Article)
            .where(Article.id == version_id, Article.parent_version_id == draft_id)
        )
        target = result.scalar_one_or_none()
        if not target:
            return None
            
        # Backup current state first
        await self.create_draft_version(db, draft_id)
        
        # Restore target version contents to main draft
        draft.title = target.title
        draft.content = target.content
        draft.outline = target.outline
        draft.secondary_keywords = target.secondary_keywords
        draft.meta_description = target.meta_description
        draft.word_count = target.word_count
        draft.status = target.status
        draft.qa_status = target.qa_status
        draft.qa_results = target.qa_results
        
        draft.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(draft)
        return draft


# Singleton instance
article_draft_service = ArticleDraftService()

