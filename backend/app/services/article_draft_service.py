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


# Singleton instance
article_draft_service = ArticleDraftService()
