"""
Seed Service for Demo Projects.

Populates demo data for new and existing projects to showcase MVP workflow.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.project import Project
from app.models.site_profile import SiteProfile
from app.models.topic_node import TopicNode
from app.models.qualification_result import QualificationResult
from app.models.article_brief import ArticleBrief
from app.models.article import Article, ArticleStatus
from app.models.content_item import ContentItem


class SeedService:
    """Service to seed demo project data."""

    async def seed_demo_data(self, db: AsyncSession, owner_id: uuid.UUID) -> dict:
        """
        Seed two demo projects: 'AI 寫作助手 (新站展示)' and 'SaaS 軟體測評網 (舊站展示)'.
        Cleans up existing projects with those exact names first to prevent duplicate pollution.
        """
        # 1. Clean up existing demo projects
        demo_names = ["AI 寫作助手 (新站展示)", "SaaS 軟體測評網 (舊站展示)"]
        for name in demo_names:
            result = await db.execute(
                select(Project).where(Project.name == name, Project.owner_id == owner_id)
            )
            existing_projects = result.scalars().all()
            for ep in existing_projects:
                await db.delete(ep)
        await db.commit()

        # 2. Seed Project 1: AI 寫作助手 (新站展示)
        project_new = Project(
            owner_id=owner_id,
            name="AI 寫作助手 (新站展示)",
            description="用於示範從 Site Profile -> Topic Map -> Topic Qualification -> Brief Builder -> AI Generation -> QA Gate 完整全新站點內容創作流程。",
            target_market="tw",
            mode="new",
            status="active",
            domain="aiwriter-demo.tw",
        )
        db.add(project_new)
        await db.commit()
        await db.refresh(project_new)

        # Site Profile for Project 1
        profile_new = SiteProfile(
            project_id=project_new.id,
            site_name="AI 寫作助手",
            business_type="SaaS 軟體服務",
            description="我們提供最先進的中文 AI 寫作工具，幫助內容創作者與企業快速生成高排名的 SEO 文章。",
            target_audience="部落客、數位行銷人員、中小企業主",
            core_topics="AI 寫作, SEO 優化, 內容行銷",
            status="ready",
        )
        db.add(profile_new)

        # Topic Nodes for Project 1
        topic_pillar = TopicNode(
            project_id=project_new.id,
            name="AI 寫作",
            topic_role="pillar",
            description="核心 Pillar 主題，涵蓋 AI 寫作技術、工具與基本概念。",
            journey_stage="awareness",
            priority="high",
            status="active",
            sort_order=1,
        )
        db.add(topic_pillar)
        await db.commit()
        await db.refresh(topic_pillar)

        topic_sub1 = TopicNode(
            project_id=project_new.id,
            parent_id=topic_pillar.id,
            name="AI 寫作技巧",
            topic_role="supporting",
            description="如何更好地寫出高流暢度的 AI 生成內容。",
            journey_stage="consideration",
            priority="medium",
            status="active",
            sort_order=1,
        )
        topic_sub2 = TopicNode(
            project_id=project_new.id,
            parent_id=topic_pillar.id,
            name="如何用 AI 寫 SEO 文章",
            topic_role="supporting",
            description="AI 與 SEO 的整合實戰操作指南。",
            journey_stage="decision",
            priority="high",
            status="active",
            sort_order=2,
        )
        db.add(topic_sub1)
        db.add(topic_sub2)
        await db.commit()
        await db.refresh(topic_sub1)
        await db.refresh(topic_sub2)

        # Topic Qualification Results
        qual1 = QualificationResult(
            project_id=project_new.id,
            input_term="AI 寫作工具推薦",
            decision="qualified",
            summary_reason="本項搜尋詞具備極高意圖（商業評估），契合本站 SaaS 寫作助手定位，且搜尋量大、競爭度中等偏高，適合作為高優先級內容建立。",
            mapped_topic_id=topic_pillar.id,
            suggested_angle="以 2026 年最新維度，評測市面上前 10 大中文 AI 寫作工具的優缺點與價格。",
            target_journey_stage="consideration",
            identity_fit="High",
            topic_fit="High",
            audience_fit="High",
            authority_fit="Medium",
            business_fit="High",
            overlap_risk="None",
            boundary_risk="None",
            review_status="approved",
        )
        qual2 = QualificationResult(
            project_id=project_new.id,
            input_term="ChatGPT 寫小說技巧",
            decision="qualified",
            summary_reason="屬於愛好者群體，雖然字詞熱度高，但對於商業轉化有一定偏差，歸類為 Supporting 內容以帶動流量。",
            mapped_topic_id=topic_sub1.id,
            suggested_angle="介紹如何設定角色卡、大綱生成以及多輪對話保持人設的小說創作技巧。",
            target_journey_stage="awareness",
            identity_fit="Medium",
            topic_fit="High",
            audience_fit="Medium",
            authority_fit="Low",
            business_fit="Medium",
            overlap_risk="None",
            boundary_risk="None",
            review_status="approved",
        )
        db.add(qual1)
        db.add(qual2)
        await db.commit()
        await db.refresh(qual1)
        await db.refresh(qual2)

        # Article Brief for qual1
        brief = ArticleBrief(
            project_id=project_new.id,
            qualification_id=qual1.id,
            mapped_topic_id=topic_pillar.id,
            title_direction="2026 最新 10 款 AI 寫作工具推薦與深度評測",
            article_role="pillar",
            search_intent="commercial",
            target_audience="行銷經理、個人創作者",
            primary_question="有哪些好用的中文 AI 寫作工具？",
            next_question="這些工具在台灣的付費管道與多語言能力表現如何？",
            info_gain_requirement="加入實際輸入相同 Prompt 後的繁體中文輸出品質對比。",
            restricted_content="避免推薦已停止維護的舊工具，且不發表偏頗的主觀評論。",
            recommended_internal_links="連結至 AI 寫作技巧指南",
            cta_direction="註冊我們的 AI 助手免費試用 14 天",
            status="approved",
        )
        db.add(brief)
        await db.commit()
        await db.refresh(brief)

        # Article Draft for brief
        article_draft = Article(
            project_id=project_new.id,
            brief_id=brief.id,
            title="2026 最新 10 款 AI 寫作工具推薦與深度評測：提升內容創作效率的終極指南",
            target_keyword="AI 寫作工具推薦",
            secondary_keywords=["AI 寫作軟體", "AI 寫作推薦", "AI 生成內容"],
            meta_description="2026 年最新 10 款繁體中文 AI 寫作工具推薦！深度剖析 ChatGPT, Claude, Copy.ai 的優劣勢與實測表現，助您輕鬆生成高品質 SEO 文章。",
            content="""在當今數位行銷與自媒體爆發的時代，內容創作的速度與品質往往是決定 Google 搜尋排名的核心。為了幫助大家提升寫作效率，本文將為您深入評測 2026 年最受歡迎的 10 款繁體中文 AI 寫作工具。

## 為什麼您需要 AI 寫作工具？
傳統的內容創作流程需要經歷資料收集、大綱草擬、正文撰寫以及重複校對，耗時費力。而 modern AI 寫作助理能在大約數秒內生成高架構的大綱與文章草稿，將創作流程縮短 70% 以上。

## 2026 年熱門 AI 寫作軟體推薦
### 1. ChatGPT
- **優勢**：對答如流、支持高度客製化 Prompt。
- **缺點**：有時會產生幻覺，需人工查證。
- **適用場景**：靈感發想、大綱擬定。

### 2. Claude
- **優勢**：繁體中文品質極佳，極富文學深度與細膩情感。
- **缺點**：付費額度消耗較快。
- **適用場景**：長文撰寫、專業產業研究報告。

## 結論與 CTA
工欲善其事，必先利其器。快來免費試用我們的 AI 寫作助手，體驗流暢、高效的內容創作流程！""",
            outline={
                "title": "2026 最新 10 款 AI 寫作工具推薦與深度評測：提升內容創作效率的終極指南",
                "meta_description": "2026 年最新 10 款繁體中文 AI 寫作工具推薦！",
                "sections": [
                    {"heading": "為什麼您需要 AI 寫作工具？", "level": 2, "key_points": ["節省時間", "靈感突破"]},
                    {"heading": "2026 年熱門 AI 寫作軟體推薦", "level": 2, "key_points": ["ChatGPT", "Claude"]},
                    {"heading": "結論與 CTA", "level": 2, "key_points": ["總結推薦"]}
                ]
            },
            word_count=650,
            version=1,
            status=ArticleStatus.REVIEW,
            qa_status="passed",
            qa_results={
                "score": 92,
                "passed": True,
                "checks": [
                    {"name": "標題包含目標關鍵字", "passed": True, "details": "已包含 'AI 寫作工具推薦'"},
                    {"name": "首段包含關鍵字", "passed": True, "details": "首段成功提及目標詞"},
                    {"name": "文章字數充足", "passed": True, "details": "650字符合基本標準"}
                ]
            }
        )
        db.add(article_draft)
        await db.commit()

        # 3. Seed Project 2: SaaS 軟體測評網 (舊站展示)
        project_exist = Project(
            owner_id=owner_id,
            name="SaaS 軟體測評網 (舊站展示)",
            description="用於展示既有網站的內容優化流程。包含導入已發布的文章網址、建立對應的主題節點，以及對既有內容進行 SEO 改進 Brief 的建立。",
            target_market="tw",
            mode="existing",
            status="SaasReview",
            domain="saasreview-demo.com",
        )
        # Note: set status="active" to make it visible
        project_exist.status = "active"
        db.add(project_exist)
        await db.commit()
        await db.refresh(project_exist)

        # Site Profile for Project 2
        profile_exist = SiteProfile(
            project_id=project_exist.id,
            site_name="SaaS 軟體測評網",
            business_type="軟體評測媒體",
            description="專業的 SaaS 軟體評測與教學網站，為亞洲企業提供客觀的工具選型建議。",
            target_audience="企業 IT 採購人員、PM、團隊領導者",
            core_topics="專案管理, 協作軟體, ERP, CRM",
            status="ready",
        )
        db.add(profile_exist)

        # Topic Nodes for Project 2
        topic_pm = TopicNode(
            project_id=project_exist.id,
            name="專案管理軟體",
            topic_role="pillar",
            description="涵蓋各種專案協作工具的比較與實務應用教學。",
            journey_stage="awareness",
            priority="high",
            status="active",
            sort_order=1,
        )
        db.add(topic_pm)
        await db.commit()
        await db.refresh(topic_pm)

        topic_asana = TopicNode(
            project_id=project_exist.id,
            parent_id=topic_pm.id,
            name="Asana 評價",
            topic_role="supporting",
            description="針對 Asana 功能、權限、價格方案的深入分析評測。",
            journey_stage="consideration",
            priority="medium",
            status="active",
            sort_order=1,
        )
        db.add(topic_asana)
        await db.commit()
        await db.refresh(topic_asana)

        # Content Items for Project 2 (Existing URLs)
        item1 = ContentItem(
            project_id=project_exist.id,
            title="Asana 教學：如何快速上手專案管理工具",
            url="https://saasreview-demo.com/asana-tutorial",
            content_type="article",
            mapped_topic_id=topic_asana.id,
            journey_stage="consideration",
            status="mapped",
            notes="舊有的基礎操作教學，目前排在 Google 第二頁，需要補充進階使用情境以獲得 Information Gain。",
        )
        item2 = ContentItem(
            project_id=project_exist.id,
            title="2025 專案管理軟體推薦：Trello, Asana, Notion 大比拼",
            url="https://saasreview-demo.com/project-management-software",
            content_type="article",
            mapped_topic_id=topic_pm.id,
            journey_stage="awareness",
            status="mapped",
            notes="大篇幅 Pillar 軟體合集文章，排名在第一頁前三名，是本站的主要流量來源。",
        )
        item3 = ContentItem(
            project_id=project_exist.id,
            title="Notion 專案管理模版分享",
            url="https://saasreview-demo.com/notion-project-template",
            content_type="article",
            mapped_topic_id=None,
            journey_stage=None,
            status="imported",
            notes="尚未對應到主題地圖中的文章項目。",
        )
        db.add(item1)
        db.add(item2)
        db.add(item3)

        # Article Brief (Optimization Brief) for Asana
        brief_opt = ArticleBrief(
            project_id=project_exist.id,
            mapped_topic_id=topic_asana.id,
            title_direction="Asana 評價：深度解析優缺點與企業團隊導入指南",
            article_role="supporting",
            search_intent="commercial",
            target_audience="專案經理、PMO、研發主管",
            primary_question="Asana 好用嗎？相比於 Jira 或 Trello 有什麼優勢？",
            next_question="Asana 的收費方案在 2026 年有沒有調整？中小團隊怎麼選最划算？",
            info_gain_requirement="補充跨部門協作中，Asana Timeline (甘特圖) 與 Portfolio (專案集) 的實戰設定步驟。",
            recommended_internal_links="連結到 Asana 教學：如何快速上手專案管理工具 (https://saasreview-demo.com/asana-tutorial)",
            status="draft",
        )
        db.add(brief_opt)
        await db.commit()

        return {
            "status": "success",
            "message": "Demo projects seeded successfully",
            "projects": [
                {"id": str(project_new.id), "name": project_new.name, "mode": project_new.mode},
                {"id": str(project_exist.id), "name": project_exist.name, "mode": project_exist.mode},
            ]
        }


seed_service = SeedService()
