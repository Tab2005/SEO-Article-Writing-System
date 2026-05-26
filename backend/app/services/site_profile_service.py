"""
Site Profile Service.

Handles site positioning configuration, status readiness, and AI-generated snapshot summary.
"""

import uuid
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.site_profile import SiteProfile
from app.services.llm_service import llm_service
from app.core.exceptions import NotFoundException, BadRequestException


class SiteProfileService:
    """Service for managing SiteProfile business logic."""

    READY_TEXT_FIELDS = (
        "site_name",
        "business_type",
        "site_description",
        "brand_voice",
    )
    READY_LIST_FIELDS = (
        "target_audiences",
        "products_or_services",
        "core_topics",
        "allowed_angles",
        "primary_goals",
    )

    @staticmethod
    def _has_non_empty_text(value: Any) -> bool:
        """Return True when a scalar field has meaningful text content."""
        return value is not None and str(value).strip() != ""

    @staticmethod
    def _has_non_empty_list(value: Any) -> bool:
        """Return True when a list field contains at least one non-empty entry."""
        if not isinstance(value, list):
            return False
        return any(str(item).strip() != "" for item in value if item is not None)

    def get_readiness_issues(self, profile: SiteProfile) -> List[str]:
        """Return the missing requirements that block the profile from ready status."""
        issues: List[str] = []

        for field_name in self.READY_TEXT_FIELDS:
            if not self._has_non_empty_text(getattr(profile, field_name, None)):
                issues.append(field_name)

        for field_name in self.READY_LIST_FIELDS:
            if not self._has_non_empty_list(getattr(profile, field_name, None)):
                issues.append(field_name)

        return issues

    def sync_status(self, profile: SiteProfile) -> Tuple[List[str], bool]:
        """Recompute and apply the canonical draft/ready status for a profile."""
        issues = self.get_readiness_issues(profile)
        next_status = "ready" if not issues else "draft"
        changed = profile.status != next_status
        profile.status = next_status
        return issues, changed

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

        self.sync_status(profile)
        
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
