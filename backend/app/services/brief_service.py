"""
Brief Service.

Handles business logic for planning article briefs, including CRUD operations
and generating briefs from qualification results.
"""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.article_brief import ArticleBrief
from app.models.qualification_result import QualificationResult
from app.models.site_profile import SiteProfile
from app.models.topic_node import TopicNode
from app.core.exceptions import NotFoundException, BadRequestException


class BriefService:
    """Service for managing ArticleBrief business logic."""

    async def list_by_project(
        self, db: AsyncSession, project_id: uuid.UUID
    ) -> List[ArticleBrief]:
        """List all article briefs for a project."""
        result = await db.execute(
            select(ArticleBrief)
            .where(ArticleBrief.project_id == project_id)
            .order_by(ArticleBrief.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_brief(
        self, db: AsyncSession, brief_id: uuid.UUID
    ) -> Optional[ArticleBrief]:
        """Get a single article brief."""
        result = await db.execute(
            select(ArticleBrief).where(ArticleBrief.id == brief_id)
        )
        return result.scalars().first()

    async def create_brief(
        self, db: AsyncSession, project_id: uuid.UUID, data: Dict[str, Any]
    ) -> ArticleBrief:
        """Create a new article brief manually."""
        brief = ArticleBrief(project_id=project_id, **data)
        db.add(brief)
        await db.commit()
        await db.refresh(brief)
        return brief

    async def update_brief(
        self, db: AsyncSession, brief_id: uuid.UUID, data: Dict[str, Any]
    ) -> ArticleBrief:
        """Update an article brief."""
        brief = await self.get_brief(db, brief_id)
        if not brief:
            raise NotFoundException("Article brief not found.")

        for key, val in data.items():
            if hasattr(brief, key):
                setattr(brief, key, val)

        await db.commit()
        await db.refresh(brief)
        return brief

    async def delete_brief(self, db: AsyncSession, brief_id: uuid.UUID) -> None:
        """Delete an article brief."""
        brief = await self.get_brief(db, brief_id)
        if not brief:
            raise NotFoundException("Article brief not found.")

        await db.delete(brief)
        await db.commit()

    async def create_from_qualification(
        self, db: AsyncSession, project_id: uuid.UUID, qualification_id: uuid.UUID
    ) -> ArticleBrief:
        """Create a structured ArticleBrief from a QualificationResult."""
        # 1. Fetch QualificationResult
        qual_res = await db.execute(
            select(QualificationResult).where(QualificationResult.id == qualification_id)
        )
        qual = qual_res.scalars().first()
        if not qual:
            raise NotFoundException("Qualification result not found.")

        # 2. Fetch SiteProfile
        profile_res = await db.execute(
            select(SiteProfile).where(SiteProfile.project_id == project_id)
        )
        profile = profile_res.scalars().first()
        if not profile:
            raise BadRequestException("Site Profile must be setup before creating brief.")

        # Fetch mapped topic node's role if available
        article_role = None
        if qual.mapped_topic_id:
            node_res = await db.execute(
                select(TopicNode).where(TopicNode.id == qual.mapped_topic_id)
            )
            node = node_res.scalars().first()
            if node:
                article_role = node.topic_role

        # Helper to join lists/strings
        def list_to_str(lst: Optional[list]) -> str:
            if not lst:
                return ""
            return ", ".join(str(x) for x in lst if x)

        target_audience = list_to_str(profile.target_audiences)
        restricted_content = list_to_str(profile.restricted_angles)
        
        # Map journey stage to search intent
        search_intent = qual.target_journey_stage
        
        # Construct brief fields
        brief = ArticleBrief(
            project_id=project_id,
            qualification_id=qualification_id,
            mapped_topic_id=qual.mapped_topic_id,
            title_direction=qual.input_term,
            article_role=article_role or "supporting",  # default to supporting
            search_intent=search_intent,
            target_audience=target_audience,
            primary_question=f"如何解決關於「{qual.input_term}」的核心痛點？",
            next_question="讀者閱讀後，接下來會面臨什麼更進階的問題？",
            info_gain_requirement=qual.suggested_angle or "請融入網站特有的觀點，提供具備資訊增益價值的寫作切角。",
            restricted_content=restricted_content or "避免提及與品牌身份無關的競爭對手或無關業務。",
            recommended_internal_links=f"建議尋找與 {qual.input_term} 相關的 Pillar (主軸) 頁面或相關文章進行內部連結。",
            cta_direction=list_to_str(profile.primary_goals) or "引導讀者至相關服務頁面或訂閱電子報。",
            status="draft"
        )
        
        db.add(brief)
        await db.commit()
        await db.refresh(brief)
        return brief


brief_service = BriefService()
