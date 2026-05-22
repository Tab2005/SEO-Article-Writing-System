"""
Site Profile Service.

Handles site positioning configuration, status readiness, and AI-generated snapshot summary.
"""

import uuid
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.site_profile import SiteProfile
from app.services.llm_service import llm_service
from app.core.exceptions import NotFoundException, BadRequestException


class SiteProfileService:
    """Service for managing SiteProfile business logic."""

    async def get_by_project(self, db: AsyncSession, project_id: uuid.UUID) -> Optional[SiteProfile]:
        """Get site profile by project ID."""
        result = await db.execute(
            select(SiteProfile).where(SiteProfile.project_id == project_id)
        )
        return result.scalars().first()

    async def create_or_update(
        self, db: AsyncSession, project_id: uuid.UUID, profile_data: Dict[str, Any]
    ) -> SiteProfile:
        """Create or update site profile for a project."""
        profile = await self.get_by_project(db, project_id)
        
        # Check if we should update or create
        if not profile:
            profile = SiteProfile(project_id=project_id, **profile_data)
            db.add(profile)
        else:
            for key, val in profile_data.items():
                if hasattr(profile, key):
                    setattr(profile, key, val)
        
        # Validate status logic
        # If site_name and business_type and site_description are provided, it can be set to ready
        required_fields = ['site_name', 'business_type', 'site_description']
        is_ready = all(
            getattr(profile, f, None) is not None and str(getattr(profile, f)).strip() != ""
            for f in required_fields
        )
        profile.status = "ready" if is_ready else "draft"
        
        await db.commit()
        await db.refresh(profile)
        return profile

    async def generate_snapshot(self, db: AsyncSession, project_id: uuid.UUID) -> SiteProfile:
        """Generate AI brand snapshot and save it."""
        profile = await self.get_by_project(db, project_id)
        if not profile:
            raise NotFoundException("Site profile not found. Please setup profile first.")
        
        # Serialize fields for LLM
        profile_dict = {
            "site_name": profile.site_name,
            "business_type": profile.business_type,
            "site_description": profile.site_description,
            "target_audiences": profile.target_audiences or [],
            "products_or_services": profile.products_or_services or [],
            "core_topics": profile.core_topics or [],
            "allowed_angles": profile.allowed_angles or [],
            "restricted_angles": profile.restricted_angles or [],
            "brand_voice": profile.brand_voice,
            "primary_goals": profile.primary_goals or []
        }
        
        # Call LLM
        snapshot = await llm_service.generate_site_snapshot(profile_dict)
        profile.summary_snapshot = snapshot
        
        await db.commit()
        await db.refresh(profile)
        return profile


site_profile_service = SiteProfileService()
