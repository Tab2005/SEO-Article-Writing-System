"""
LLM Service.

Handles AI Hub integration for content generation.
Uses AI Hub module for unified access to multiple AI providers.
"""

import json
import asyncio
from typing import Optional, List, Dict, Any
from functools import partial

from app.config import settings
from app.core.exceptions import ExternalServiceException, BadRequestException
from app.schemas.article import ArticleOutline, OutlineSection
from app.services.ai.zeabur_client import ZeaburAIClient
from app.services.ai.gemini_client import GoogleGeminiClient
from app.services.runtime_settings import get_ai_config


class LLMService:
    """Service for AI Hub integration."""

    def __init__(self):
        self._zeabur_client: Optional[ZeaburAIClient] = None
        self._gemini_client: Optional[GoogleGeminiClient] = None
        self._zeabur_api_key: Optional[str] = None
        self._gemini_api_key: Optional[str] = None

    async def _get_client(self, provider: str, api_key: Optional[str]):
        """Get or create AI client based on provider (runtime-configurable)."""
        if not api_key:
            raise BadRequestException(
                "AI API not configured. Please set AI_API_KEY in settings or environment variable."
            )

        if provider == "zeabur":
            if self._zeabur_client is None or self._zeabur_api_key != api_key:
                self._zeabur_client = ZeaburAIClient(api_key=api_key)
                self._zeabur_api_key = api_key
            return self._zeabur_client

        if provider == "google_gemini":
            if self._gemini_client is None or self._gemini_api_key != api_key:
                self._gemini_client = GoogleGeminiClient(api_key=api_key)
                self._gemini_api_key = api_key
            return self._gemini_client

        raise BadRequestException(f"Unsupported AI provider: {provider}")

    async def _generate_with_ai(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        Generate content using AI Hub.

        Args:
            system_prompt: System instructions
            user_prompt: User input
            temperature: Generation temperature
            response_format: Optional format specification (e.g., {"type": "json_object"})

        Returns:
            Generated text
        """
        provider, model, api_key = await get_ai_config()
        
        if settings.debug and not api_key:
            if response_format and response_format.get("type") == "json_object":
                if "is_passed" in system_prompt or "qa" in system_prompt.lower():
                    return json.dumps({
                        "is_passed": True,
                        "issues": [
                            {
                                "check_type": "info_gain",
                                "severity": "warning",
                                "description": "文章包含了核心的說明，但可以再加入更多數據支撐以提升資訊增益。",
                                "suggestion": "建議在第二章節中加入1-2個行業數據或實際案例說明。"
                            }
                        ]
                    })
                if "decision" in system_prompt or "qualification" in system_prompt or "評估" in system_prompt:
                    return json.dumps({
                        "decision": "qualified",
                        "summary_reason": "這是一個模擬的評估結果，該主題非常契合網站定位與核心受眾需求。",
                        "suggested_angle": "探討實用工具、優缺點分析與工作流整合",
                        "target_journey_stage": "consideration",
                        "identity_fit": "High",
                        "topic_fit": "High",
                        "audience_fit": "High",
                        "authority_fit": "High",
                        "business_fit": "High",
                        "overlap_risk": "None",
                        "boundary_risk": "None",
                        "risks": [],
                        "alternative_topics": [],
                        "recommended_next_step": "建立文章任務書 Brief 以規劃寫作"
                    })
                return json.dumps({
                    "title": f"模擬文章大綱: 關於主題",
                    "meta_description": f"這是一篇為測試模擬大綱所生成的 Meta 描述。",
                    "sections": [
                        {
                            "heading": "一、引言與核心背景",
                            "level": 2,
                            "key_points": ["概念定義", "背景介紹"],
                            "subsections": []
                        },
                        {
                            "heading": "二、核心技巧與最佳實踐",
                            "level": 2,
                            "key_points": ["實作步驟", "注意事項"],
                            "subsections": []
                        }
                    ],
                    "estimated_word_count": 2000,
                    "target_keywords": ["模擬關鍵字"]
                })
            return f"# 模擬文章內容\n\n這是在偵錯/測試模式下，沒有設定 API 金鑰時，系統模擬生成的內容。"

        client = await self._get_client(provider=provider, api_key=api_key)

        # Add JSON instruction if response format is specified
        if response_format and response_format.get("type") == "json_object":
            system_prompt += "\n\nIMPORTANT: You must respond with valid JSON only. No additional text or explanation."

        try:
            # Both clients support generate_content with similar interface
            # Run in thread pool since clients are synchronous
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(
                None,
                partial(
                    client.generate_content,
                    prompt=user_prompt,
                    model=model,
                    system_prompt=system_prompt,
                    temperature=temperature
                )
            )
            return content
        except Exception as e:
            raise ExternalServiceException(f"AI generation error: {str(e)}")

    async def generate_outline(
        self,
        topic: str,
        target_keyword: str,
        secondary_keywords: Optional[List[str]] = None,
        competitor_h2s: Optional[List[str]] = None,
        word_count_target: int = 2000,
        tone: str = "professional",
        brief_data: Optional[Any] = None,
    ) -> ArticleOutline:
        """
        Generate SEO-optimized article outline.

        Args:
            topic: Article topic
            target_keyword: Main SEO keyword
            secondary_keywords: Additional keywords to include
            competitor_h2s: Common H2 headings from competitors
            word_count_target: Target word count
            tone: Writing tone
            brief_data: ArticleBrief data for strategic constraints

        Returns:
            ArticleOutline with structured sections
        """
        competitor_context = ""
        if competitor_h2s:
            competitor_context = f"\n\n競爭對手常見的 H2 標題：\n" + "\n".join(f"- {h}" for h in competitor_h2s[:10])

        brief_context = ""
        if brief_data:
            brief_context = f"""
[文章任務書策略約束]：
- 目標受眾：{getattr(brief_data, 'target_audience', '無') or '無'}
- 文章定位角色：{getattr(brief_data, 'article_role', '無') or '無'}
- 搜尋意圖：{getattr(brief_data, 'search_intent', '無') or '無'}
- 核心解答問題：{getattr(brief_data, 'primary_question', '無') or '無'}
- 下一步追問問題：{getattr(brief_data, 'next_question', '無') or '無'}
- 資訊增益要求：{getattr(brief_data, 'info_gain_requirement', '無') or '無'}
- 禁用與邊界內容：{getattr(brief_data, 'restricted_content', '無') or '無'}
- CTA 導向：{getattr(brief_data, 'cta_direction', '無') or '無'}
"""

        system_prompt = f"""你是一位專業的 SEO 內容策略師。你的任務是根據目標關鍵字、任務書約束和競品分析，生成一個優化的文章大綱。
{brief_context}
請務必嚴格遵守 [文章任務書策略約束]。特別是其中的『禁用與邊界內容』絕對不可出現在大綱中，『主要解答問題』與『次要解答問題』必須在大綱的主要段落或 H2/H3 中明確提及並提出解答方案，且符合『資訊增益要求』。

請以 JSON 格式回傳大綱，結構如下：
{{
    "title": "文章標題（包含關鍵字）",
    "meta_description": "150字以內的 SEO 描述",
    "sections": [
        {{
            "heading": "H2 標題",
            "level": 2,
            "key_points": ["要點1", "要點2"],
            "subsections": [
                {{
                    "heading": "H3 標題",
                    "level": 3,
                    "key_points": ["要點1"],
                    "subsections": []
                }}
            ]
        }}
    ],
    "estimated_word_count": 2000,
    "target_keywords": ["主關鍵字", "長尾關鍵字1", "長尾關鍵字2"]
}}"""

        secondary_context = ""
        if secondary_keywords:
            secondary_context = f"\n次要關鍵字：{', '.join(secondary_keywords)}"

        user_prompt = f"""請為以下主題生成一個 SEO 優化的文章大綱：

主題：{topic}
目標關鍵字：{target_keyword}{secondary_context}
目標字數：{word_count_target} 字
寫作風格：{tone}
{competitor_context}

請確保：
1. 標題和 H2 標題都包含目標關鍵字或相關變體
2. 大綱結構清晰，易於閱讀
3. 包含常見問題 (FAQ) 段落
4. 涵蓋競爭對手的重要主題，但要有獨特觀點
5. 自然融入次要關鍵字"""

        try:
            content = await self._generate_with_ai(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            data = json.loads(content)

            # Parse sections recursively
            def parse_section(section_data: Dict[str, Any]) -> OutlineSection:
                return OutlineSection(
                    heading=section_data.get("heading", ""),
                    level=section_data.get("level", 2),
                    key_points=section_data.get("key_points", []),
                    subsections=[
                        parse_section(sub) for sub in section_data.get("subsections", [])
                    ],
                )

            sections = [parse_section(s) for s in data.get("sections", [])]

            return ArticleOutline(
                title=data.get("title", topic),
                meta_description=data.get("meta_description", ""),
                sections=sections,
                estimated_word_count=data.get("estimated_word_count", word_count_target),
                target_keywords=data.get("target_keywords", [target_keyword]),
            )

        except json.JSONDecodeError as e:
            raise ExternalServiceException(f"Failed to parse LLM response: {e}")
        except Exception as e:
            raise ExternalServiceException(f"AI API error: {str(e)}")

    async def generate_section_content(
        self,
        section: OutlineSection,
        context: str = "",
        target_keyword: str = "",
    ) -> str:
        """
        Generate content for a single section.

        Args:
            section: OutlineSection to expand
            context: Additional context (article summary, etc.)
            target_keyword: Main keyword for SEO

        Returns:
            Generated markdown content
        """
        key_points_text = "\n".join(f"- {point}" for point in section.key_points)

        system_prompt = """你是一位專業的 SEO 內容作家。你的任務是根據大綱段落生成高質量的內容。

寫作準則：
1. 使用自然流暢的繁體中文
2. 適當融入關鍵字，但不要過度堆砌
3. 段落清晰，易於閱讀
4. 使用 Markdown 格式
5. 每段 150-200 字為宜"""

        user_prompt = f"""請為以下段落生成詳細內容：

標題：{section.heading}
層級：H{section.level}
目標關鍵字：{target_keyword}

要涵蓋的要點：
{key_points_text}

{f"上下文：{context}" if context else ""}

請直接輸出 Markdown 格式的內容，以適當的標題開始。"""

        try:
            content = await self._generate_with_ai(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            )

            return content or ""

        except Exception as e:
            raise ExternalServiceException(f"AI API error: {str(e)}")

    async def generate_full_article(
        self,
        outline: ArticleOutline,
        target_keyword: str,
        secondary_keywords: Optional[List[str]] = None,
        brief_data: Optional[Any] = None,
    ) -> str:
        """
        Generate complete article from outline.

        Args:
            outline: Complete article outline
            target_keyword: Main SEO keyword
            secondary_keywords: Additional keywords to include
            brief_data: ArticleBrief data for strategic constraints

        Returns:
            Full article in Markdown format
        """
        # Format outline for prompt
        outline_text = f"# {outline.title}\n\n"

        def format_section(section: OutlineSection, indent: int = 0) -> str:
            prefix = "  " * indent
            result = f"{prefix}- {section.heading}\n"
            for point in section.key_points:
                result += f"{prefix}  - {point}\n"
            for sub in section.subsections:
                result += format_section(sub, indent + 1)
            return result

        for section in outline.sections:
            outline_text += format_section(section)

        system_prompt = """你是一位專業的 SEO 內容作家。你的任務是根據提供的大綱生成完整的文章。

寫作準則：
1. 使用自然流暢的繁體中文
2. 適當融入關鍵字，密度約 1-2%
3. 使用 Markdown 格式，包含適當的標題層級
4. 每個段落 150-200 字
5. 包含引人入勝的開頭和總結
6. 在適當位置添加重點標示（粗體、項目符號等）"""

        secondary_text = ""
        if secondary_keywords:
            secondary_text = f"\n次要關鍵字：{', '.join(secondary_keywords)}"

        user_prompt = f"""請根據以下大綱生成一篇完整的 SEO 文章：

目標關鍵字：{target_keyword}{secondary_text}
Meta 描述：{outline.meta_description}
目標字數：{outline.estimated_word_count}

大綱：
{outline_text}

請直接輸出完整的 Markdown 格式文章，不需要任何額外說明。
確保自然融入所有目標關鍵字。"""

        try:
            content = await self._generate_with_ai(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            )

            return content or ""

        except Exception as e:
            raise ExternalServiceException(f"AI API error: {str(e)}")

    async def optimize_content(
        self,
        content: str,
        target_keywords: List[str],
    ) -> str:
        """
        Optimize existing content for SEO.

        Args:
            content: Original content
            target_keywords: Keywords to optimize for

        Returns:
            Optimized content
        """
        keywords_text = ", ".join(target_keywords)

        system_prompt = """你是一位 SEO 專家。你的任務是優化文章內容以提高搜尋引擎排名。

優化重點：
1. 自然融入目標關鍵字
2. 改善內容結構
3. 增加相關的長尾關鍵字
4. 確保內容易於閱讀
5. 保持原文的核心訊息"""

        user_prompt = f"""請優化以下文章內容：

目標關鍵字：{keywords_text}

原始內容：
{content}

請返回優化後的 Markdown 格式內容。"""

        try:
            optimized = await self._generate_with_ai(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5
            )

            return optimized or content

        except Exception as e:
            raise ExternalServiceException(f"AI API error: {str(e)}")

    async def extract_themes(
        self,
        headings_by_competitor: List[List[str]],
        keyword: str,
        top_n: int = 8,
    ) -> List[Dict[str, Any]]:
        """
        Extract semantic topic themes from competitor headings using LLM.

        Args:
            headings_by_competitor: List of heading lists, one per competitor
            keyword: Target keyword for context
            top_n: Number of themes to return

        Returns:
            List of theme dictionaries with name, coverage, and examples
        """
        # Flatten and prepare headings with competitor index
        all_headings_text = ""
        total_competitors = len([h for h in headings_by_competitor if h])

        for i, headings in enumerate(headings_by_competitor):
            if headings:
                all_headings_text += f"\n競爭者 {i+1}:\n"
                for h in headings[:8]:  # Limit per competitor
                    all_headings_text += f"  - {h}\n"

        if not all_headings_text.strip():
            return []

        system_prompt = """你是一位 SEO 專家。分析競爭者文章的 H2 標題，歸納出語意主題類別。

請以 JSON 格式回傳主題分析結果：
{
    "themes": [
        {
            "theme_name": "主題名稱（2-4個字）",
            "coverage_count": 3,
            "example_headings": ["標題1", "標題2"]
        }
    ]
}

注意：
1. 主題名稱應該簡短、具有概括性（如「步驟流程」「工具推薦」「定義說明」「比較評測」）
2. coverage_count 是有多少個競爭者涵蓋這個主題
3. example_headings 是屬於這個主題的2-3個範例標題"""

        user_prompt = f"""請分析以下 {total_competitors} 個競爭者的 H2 標題，找出主要的語意主題：

目標關鍵字：{keyword}

競爭者標題：
{all_headings_text}

請歸納出最重要的 {top_n} 個主題類別。"""

        try:
            content = await self._generate_with_ai(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            data = json.loads(content)

            themes = data.get("themes", [])

            # Add total_competitors to each theme
            for theme in themes:
                theme["total_competitors"] = total_competitors

            return themes[:top_n]

        except json.JSONDecodeError:
            return []
        except Exception as e:
            # Return empty list on error, don't fail the whole analysis
            return []

    async def generate_site_snapshot(self, profile_data: Dict[str, Any]) -> str:
        """Generate a short positioning summary snapshot of the website identity."""
        system_prompt = """你是一位專業的 SEO 與品牌策略顧問。你的任務是將提供的網站設定（Site Profile）整合成一個精煉、有力且高度一致的「品牌定位 snapshot」（大約 150-250 字）。
這段摘要將作為後續 AI 題目判定與內容生成時的核心品牌引導。請確保能總結該網站在市場中的獨特角色、核心主題、以及其主要受眾與禁忌。"""
        
        user_prompt = f"""請根據以下網站設定（Site Profile）生成品牌定位 Snapshot 摘要：
- 網站名稱: {profile_data.get('site_name', '未命名')}
- 業務類型/產業: {profile_data.get('business_type', '未填寫')}
- 網站描述: {profile_data.get('site_description', '未填寫')}
- 目標受眾: {', '.join(profile_data.get('target_audiences') or [])}
- 核心服務或產品: {', '.join(profile_data.get('products_or_services') or [])}
- 核心涵蓋主題: {', '.join(profile_data.get('core_topics') or [])}
- 品牌語調: {profile_data.get('brand_voice', '未填寫')}
- 偏好的寫作角度/切角: {', '.join(profile_data.get('allowed_angles') or [])}
- 嚴格禁止的寫作角度/切角: {', '.join(profile_data.get('restricted_angles') or [])}
- 主要目標: {', '.join(profile_data.get('primary_goals') or [])}

請以繁體中文撰寫，直接輸出 Snapshot 文字，不需要任何引言或 Markdown 裝飾。"""

        try:
            snapshot = await self._generate_with_ai(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5
            )
            return snapshot.strip() if snapshot else ""
        except Exception as e:
            raise ExternalServiceException(f"AI API error during snapshot generation: {str(e)}")

    async def evaluate_qualification(
        self,
        input_term: str,
        site_profile: Dict[str, Any],
        topic_nodes_context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluate a candidate keyword/topic idea using LLM for suitability."""
        system_prompt = """你是一位 SEO 題目判定專家。你的任務是評估一個候選主題/關鍵字，是否適合該品牌網站進行內容創作。
你必須以 JSON 格式回傳評估結果，格式如下：
{
    "decision": "qualified 或 not_qualified 之一",
    "summary_reason": "判定決策的繁體中文扼要說明",
    "suggested_angle": "如果 qualified，建議本網站在撰寫此主題時的獨特且安全的切角；若為 not_qualified，寫為 null",
    "target_journey_stage": "awareness, consideration, decision 之一，或為 null",
    "identity_fit": "High, Medium, Low 之一",
    "topic_fit": "High, Medium, Low 之一",
    "audience_fit": "High, Medium, Low 之一",
    "authority_fit": "High, Medium, Low 之一",
    "business_fit": "High, Medium, Low 之一",
    "overlap_risk": "High, Medium, Low, None 之一",
    "boundary_risk": "High, Medium, Low, None 之一",
    "risks": ["具體的風險點1", "具體的風險點2（若無，為空陣列）"],
    "alternative_topics": ["如果 not_qualified，推薦2-3個更合適、更貼近網站定位的核心替代主題（若無，為空陣列）"],
    "recommended_next_step": "下一步建議行動的繁體中文說明"
}

重要評估維度說明：
1. identity_fit: 主題是否契合品牌定位。
2. topic_fit: 是否契合核心主題樹。
3. audience_fit: 是否能吸引目標受眾。
4. authority_fit: 品牌是否有足夠專業度或舉證資產寫此主題。
5. business_fit: 寫此主題是否對品牌商業目標有助益。
6. overlap_risk: 與既有主題或內容是否高度重疊。
7. boundary_risk: 是否觸及網站明文禁止的敏感或限制切角（Restricted Angles）。
注意：如果 boundary_risk 為 High，或者是觸及了 Restricted Angles，你必須果斷判定為 not_qualified！"""

        # Format topic map context for prompt
        topic_map_str = "\n".join([
            f"- {node['name']} (角色: {node['role']}, 階段: {node['journey_stage']})"
            for node in topic_nodes_context
        ]) if topic_nodes_context else "（目前尚未建立主題地圖）"

        user_prompt = f"""請評估以下候選關鍵字/主題：
【候選主題】：{input_term}

【網站定位設定】：
- 品牌名稱與定位 Snapshot: {site_profile.get('summary_snapshot', '未生成')}
- 核心主題: {', '.join(site_profile.get('core_topics') or [])}
- 目標受眾: {', '.join(site_profile.get('target_audiences') or [])}
- 偏好切角 (Allowed Angles): {', '.join(site_profile.get('allowed_angles') or [])}
- 嚴格禁止的切角 (Restricted Angles): {', '.join(site_profile.get('restricted_angles') or [])}
- 舉證資產 (Proof Assets): {', '.join(site_profile.get('proof_assets') or [])}

【既有主題地圖上下文】：
{topic_map_str}

請嚴格進行判定，並以指定的 JSON 格式回傳，請確保回傳的內容都是繁體中文。"""

        try:
            content = await self._generate_with_ai(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ExternalServiceException(f"Failed to parse LLM evaluation response: {e}")
        except Exception as e:
            raise ExternalServiceException(f"AI evaluation service error: {str(e)}")


# Singleton instance
llm_service = LLMService()
