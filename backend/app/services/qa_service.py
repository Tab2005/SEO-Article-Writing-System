"""
QA Service.

Implements the QA Gate V1 content auditing engine.
Audits generated content against Site Profile and Article Brief requirements.
"""

import uuid
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.article import Article
from app.models.article_brief import ArticleBrief
from app.models.site_profile import SiteProfile
from app.services.llm_service import llm_service
from app.core.exceptions import NotFoundException, BadRequestException


class QAService:
    """Service for running QA Gate checks on article drafts."""

    async def run_qa(self, db: AsyncSession, draft_id: uuid.UUID) -> Article:
        """
        Run QA Gate V1 auditing on a draft.
        
        Loads draft, associated brief, and site profile.
        Invokes LLM to check content compliance and updates DB.
        """
        # 1. Load Article Draft
        result = await db.execute(select(Article).where(Article.id == draft_id))
        article = result.scalar_one_or_none()
        if not article:
            raise NotFoundException("Article draft not found.")

        # 2. Load Site Profile
        profile_res = await db.execute(
            select(SiteProfile).where(SiteProfile.project_id == article.project_id)
        )
        profile = profile_res.scalars().first()
        if not profile:
            raise BadRequestException("Site Profile must be setup before running QA checks.")

        # 3. Load Article Brief (optional, but highly recommended)
        brief = None
        if article.brief_id:
            brief_res = await db.execute(
                select(ArticleBrief).where(ArticleBrief.id == article.brief_id)
            )
            brief = brief_res.scalars().first()

        # 4. Prepare system prompt and user prompt for LLM evaluation
        system_prompt = """你是一位專業的 SEO 內容品質稽核專家 (QA Auditor)。
你的任務是根據「網站定位設定」與「文章任務書 (Brief) 約束」，對生成好的文章草稿進行嚴格的品質與合規性審查 (QA Gate V1)。

你必須評估以下四個面向：
1. 網站定位契合度 (Identity Fit): 比對網站定位描述，評估文章是否有偏離核心主題或受眾定位的內容。
2. 禁用內容邊界檢查 (Restricted Angles): 比對網站禁用切角與文章任務書的禁用內容，檢視文章中是否含有禁止或越界的字眼與主題。
3. 資訊增益要求 (Info Gain Requirement): 評估文章是否包含任務書中規定的獨特論點、數據、專業見解或增益內容，而非僅是 AI 廢話。
4. CTA 導向檢查 (CTA Direction): 檢查文章結尾是否正確包含了導引 CTA，且方向符合任務書要求。

你必須以 JSON 格式回傳評估結果，格式如下：
{
    "is_passed": true 或 false (若 issues 中有任何一個 severity 為 "error" 的問題，必須為 false；若只有 "warning" 或是沒有問題，則為 true),
    "issues": [
        {
            "check_type": "identity", "restricted", "info_gain", "cta" 之一,
            "severity": "error" (拒絕/必須修正) 或 "warning" (警告/建議優化) 之一,
            "description": "具體發現的問題陳述，請用繁體中文",
            "suggestion": "具體的優化改善建議，請用繁體中文"
        }
    ]
}

請確保回傳的內容都是繁體中文。若無任何問題，issues 請回傳空陣列，is_passed 回傳 true。"""

        # Build Site Profile Info
        profile_info = f"""- 品牌名稱與定位 Snapshot: {profile.summary_snapshot or '未生成'}
- 核心主題: {', '.join(profile.core_topics or [])}
- 目標受眾: {', '.join(profile.target_audiences or [])}
- 偏好切角 (Allowed Angles): {', '.join(profile.allowed_angles or [])}
- 嚴格禁止的切角 (Restricted Angles): {', '.join(profile.restricted_angles or [])}"""

        # Build Brief Info
        if brief:
            brief_info = f"""- 標題與寫作方向 (Title Direction): {brief.title_direction}
- 搜尋意圖 (Search Intent): {brief.search_intent or '未指定'}
- 讀者受眾 (Target Audience): {brief.target_audience or '未指定'}
- 核心問題 (Primary & Next Question): {brief.primary_question or '無'} / {brief.next_question or '無'}
- 資訊增益要求 (Info Gain Requirement): {brief.info_gain_requirement or '無'}
- 禁用寫作切角與內容 (Restricted Content): {brief.restricted_content or '無'}
- CTA 導向 (CTA Direction): {brief.cta_direction or '無'}"""
        else:
            brief_info = "（本草稿未綁定文章任務書 Brief）"

        user_prompt = f"""請對以下文章草稿進行 QA 審查。

【網站定位設定】：
{profile_info}

【文章任務書 Brief】：
{brief_info}

【文章標題】：{article.title}
【文章目標關鍵字】：{article.target_keyword}
【文章內文】：
{article.content or '（文章內容為空）'}

請嚴格進行審查，並以指定的 JSON 格式回傳評估報告。請確保回傳的字詞與描述皆使用繁體中文。"""

        # 5. Call LLM Service
        try:
            content_out = await llm_service._generate_with_ai(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            qa_res = json.loads(content_out)
        except json.JSONDecodeError as e:
            # Fallback if JSON parse fails
            qa_res = {
                "is_passed": False,
                "issues": [
                    {
                        "check_type": "identity",
                        "severity": "error",
                        "description": f"解析 QA 評估結果失敗: {str(e)}",
                        "suggestion": "請重新執行 QA 審查。"
                    }
                ]
            }
        except Exception as e:
            qa_res = {
                "is_passed": False,
                "issues": [
                    {
                        "check_type": "identity",
                        "severity": "error",
                        "description": f"執行 QA 審查時發生錯誤: {str(e)}",
                        "suggestion": "請檢查 AI 服務連接與設定。"
                    }
                ]
            }

        # 6. Update Article model
        is_passed = qa_res.get("is_passed", True)
        article.qa_status = "passed" if is_passed else "failed"
        article.qa_results = qa_res

        db.add(article)
        await db.commit()
        await db.refresh(article)

        return article


# Singleton instance
qa_service = QAService()
