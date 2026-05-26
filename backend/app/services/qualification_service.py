"""
Qualification Service.

Implements the evaluation engine including hard filters, content overlap checks, and LLM rating checks.
"""

import uuid
import difflib
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.qualification_result import QualificationResult
from app.models.site_profile import SiteProfile
from app.models.content_item import ContentItem
from app.models.topic_node import TopicNode
from app.models.project import Project
from app.services.llm_service import llm_service
from app.services.site_profile_service import site_profile_service
from app.core.exceptions import NotFoundException, BadRequestException


class QualificationService:
    """Service for checking content qualification and duplicate checks."""

    async def list_by_project(
        self, db: AsyncSession, project_id: uuid.UUID
    ) -> List[QualificationResult]:
        """List all qualification results for a project."""
        result = await db.execute(
            select(QualificationResult)
            .where(QualificationResult.project_id == project_id)
            .order_by(QualificationResult.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_result(
        self, db: AsyncSession, result_id: uuid.UUID
    ) -> Optional[QualificationResult]:
        """Get a single qualification result."""
        result = await db.execute(
            select(QualificationResult).where(QualificationResult.id == result_id)
        )
        return result.scalars().first()

    async def evaluate_topic(
        self, db: AsyncSession, project_id: uuid.UUID, input_term: str
    ) -> QualificationResult:
        """Run the multi-stage qualification rules and return evaluation result."""
        # 0. Load Project, Site Profile, and Topic Nodes
        project_res = await db.execute(select(Project).where(Project.id == project_id))
        project = project_res.scalars().first()
        if not project:
            raise NotFoundException("Project not found.")
        if project.status != "active":
            raise BadRequestException("Project must be active before evaluating topics.")

        profile_res = await db.execute(
            select(SiteProfile).where(SiteProfile.project_id == project_id)
        )
        profile = profile_res.scalars().first()
        if not profile:
            raise BadRequestException("Site Profile must be setup before evaluating topics.")
        readiness_issues, status_changed = site_profile_service.sync_status(profile)
        if status_changed:
            await db.commit()
            await db.refresh(profile)
        if readiness_issues:
            missing_fields = ", ".join(readiness_issues)
            raise BadRequestException(
                f"Site Profile must be ready before evaluating topics. Missing required fields: {missing_fields}."
            )

        # Fetch active topic nodes context
        nodes_res = await db.execute(
            select(TopicNode).where(TopicNode.project_id == project_id)
        )
        nodes = list(nodes_res.scalars().all())
        active_nodes = [node for node in nodes if node.status == "active"]
        if not active_nodes:
            raise BadRequestException(
                "Topic Map must contain at least one active Topic Node before evaluating topics."
            )

        # Step 1: Hard Filter Checks (Restricted Angles)
        restricted = profile.restricted_angles or []
        for term in restricted:
            if term.strip() and term.lower() in input_term.lower():
                # Direct reject
                eval_res = QualificationResult(
                    project_id=project_id,
                    input_term=input_term,
                    decision="not_qualified",
                    summary_reason=f"硬性規則攔截：候選題目包含禁止寫作切角關鍵字『{term}』。",
                    identity_fit="Low",
                    topic_fit="Low",
                    audience_fit="Low",
                    authority_fit="Low",
                    business_fit="Low",
                    overlap_risk="None",
                    boundary_risk="High",
                    risks=["觸及 Restricted Angles 禁忌主題"],
                    alternative_topics=[],
                    recommended_next_step="排除此題目，或修改切角以符合品牌限制。",
                    review_status="generated"
                )
                db.add(eval_res)
                await db.commit()
                await db.refresh(eval_res)
                return eval_res

        # Step 2: Content Overlap check (only for existing_site mode)
        if project.mode == "existing_site":
            content_items_res = await db.execute(
                select(ContentItem).where(ContentItem.project_id == project_id)
            )
            content_items = list(content_items_res.scalars().all())
            
            best_match: Optional[ContentItem] = None
            best_ratio = 0.0
            
            for item in content_items:
                # Use difflib to compare string similarity
                ratio = difflib.SequenceMatcher(None, input_term.lower(), item.title.lower()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = item
                    
            # Threshold: 0.7 similarity is treated as a duplicate overlap
            if best_ratio >= 0.7 and best_match:
                eval_res = QualificationResult(
                    project_id=project_id,
                    input_term=input_term,
                    decision="rewrite_existing",
                    summary_reason=f"內容重複警告：此主題與您已匯入的舊文章『{best_match.title}』相似度達 {int(best_ratio*100)}%。",
                    mapped_topic_id=best_match.mapped_topic_id,
                    suggested_angle=f"建議對現有文章進行改寫，而非新建獨立文章。融入新的觀點或時效資訊。",
                    target_journey_stage=best_match.journey_stage or "awareness",
                    identity_fit="High",
                    topic_fit="High",
                    audience_fit="High",
                    authority_fit="High",
                    business_fit="Medium",
                    overlap_risk="High",
                    boundary_risk="None",
                    risks=[f"與既有 URL {best_match.url or '未填'} 內容高度重疊"],
                    alternative_topics=[],
                    recommended_next_step="跳轉至文章編輯器，對現有文章規劃優化改寫版本。",
                    review_status="generated"
                )
                db.add(eval_res)
                await db.commit()
                await db.refresh(eval_res)
                return eval_res

        # Step 3: LLM Suitability Check
        profile_dict = {
            "summary_snapshot": profile.summary_snapshot,
            "core_topics": profile.core_topics or [],
            "target_audiences": profile.target_audiences or [],
            "allowed_angles": profile.allowed_angles or [],
            "restricted_angles": profile.restricted_angles or [],
            "proof_assets": profile.proof_assets or []
        }
        
        topic_nodes_context = [
            {"name": n.name, "role": n.topic_role, "journey_stage": n.journey_stage}
            for n in active_nodes
        ]
        
        # LLM evaluate
        llm_out = await llm_service.evaluate_qualification(
            input_term=input_term,
            site_profile=profile_dict,
            topic_nodes_context=topic_nodes_context
        )
        
        # Auto-match to an existing topic node if one shares the name exactly
        mapped_node_id: Optional[uuid.UUID] = None
        for n in active_nodes:
            if n.name.lower() in input_term.lower() or input_term.lower() in n.name.lower():
                mapped_node_id = n.id
                break

        eval_res = QualificationResult(
            project_id=project_id,
            input_term=input_term,
            decision=llm_out.get("decision", "qualified"),
            summary_reason=llm_out.get("summary_reason"),
            mapped_topic_id=mapped_node_id,
            suggested_angle=llm_out.get("suggested_angle"),
            target_journey_stage=llm_out.get("target_journey_stage"),
            identity_fit=llm_out.get("identity_fit"),
            topic_fit=llm_out.get("topic_fit"),
            audience_fit=llm_out.get("audience_fit"),
            authority_fit=llm_out.get("authority_fit"),
            business_fit=llm_out.get("business_fit"),
            overlap_risk=llm_out.get("overlap_risk", "None"),
            boundary_risk=llm_out.get("boundary_risk", "None"),
            risks=llm_out.get("risks", []),
            alternative_topics=llm_out.get("alternative_topics", []),
            recommended_next_step=llm_out.get("recommended_next_step"),
            review_status="generated"
        )
        db.add(eval_res)
        await db.commit()
        await db.refresh(eval_res)
        return eval_res

    async def update_result(
        self, db: AsyncSession, result_id: uuid.UUID, update_data: Dict[str, Any]
    ) -> QualificationResult:
        """Update review status or change details of an evaluation result."""
        result = await self.get_result(db, result_id)
        if not result:
            raise NotFoundException("Qualification result not found.")
            
        for key, val in update_data.items():
            if hasattr(result, key):
                setattr(result, key, val)
                
        await db.commit()
        await db.refresh(result)
        return result


qualification_service = QualificationService()
