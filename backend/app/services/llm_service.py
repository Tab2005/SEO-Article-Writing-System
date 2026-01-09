"""
LLM Service.

Handles OpenAI API integration for content generation.
"""

import json
from typing import Optional, List, Dict, Any

from openai import AsyncOpenAI

from app.config import settings
from app.core.exceptions import ExternalServiceException, BadRequestException
from app.schemas.article import ArticleOutline, OutlineSection


class LLMService:
    """Service for OpenAI GPT integration."""
    
    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None
        self.model = settings.openai_model
    
    def _get_client(self) -> AsyncOpenAI:
        """Get or create OpenAI client."""
        if not settings.openai_api_key:
            raise BadRequestException(
                "OpenAI API not configured. Please set OPENAI_API_KEY environment variable."
            )
        
        if self._client is None:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client
    
    async def generate_outline(
        self,
        topic: str,
        target_keyword: str,
        competitor_h2s: Optional[List[str]] = None,
        word_count_target: int = 2000,
        tone: str = "professional",
    ) -> ArticleOutline:
        """
        Generate SEO-optimized article outline.
        
        Args:
            topic: Article topic
            target_keyword: Main SEO keyword
            competitor_h2s: Common H2 headings from competitors
            word_count_target: Target word count
            tone: Writing tone
            
        Returns:
            ArticleOutline with structured sections
        """
        client = self._get_client()
        
        competitor_context = ""
        if competitor_h2s:
            competitor_context = f"\n\n競爭對手常見的 H2 標題：\n" + "\n".join(f"- {h}" for h in competitor_h2s[:10])
        
        system_prompt = """你是一位專業的 SEO 內容策略師。你的任務是根據目標關鍵字和競品分析，生成一個優化的文章大綱。

請以 JSON 格式回傳大綱，結構如下：
{
    "title": "文章標題（包含關鍵字）",
    "meta_description": "150字以內的 SEO 描述",
    "sections": [
        {
            "heading": "H2 標題",
            "level": 2,
            "key_points": ["要點1", "要點2"],
            "subsections": [
                {
                    "heading": "H3 標題",
                    "level": 3,
                    "key_points": ["要點1"],
                    "subsections": []
                }
            ]
        }
    ],
    "estimated_word_count": 2000,
    "target_keywords": ["主關鍵字", "長尾關鍵字1", "長尾關鍵字2"]
}"""

        user_prompt = f"""請為以下主題生成一個 SEO 優化的文章大綱：

主題：{topic}
目標關鍵字：{target_keyword}
目標字數：{word_count_target} 字
寫作風格：{tone}
{competitor_context}

請確保：
1. 標題和 H2 標題都包含目標關鍵字或相關變體
2. 大綱結構清晰，易於閱讀
3. 包含常見問題 (FAQ) 段落
4. 涵蓋競爭對手的重要主題，但要有獨特觀點"""

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
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
            raise ExternalServiceException(f"OpenAI API error: {str(e)}")
    
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
        client = self._get_client()
        
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
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            raise ExternalServiceException(f"OpenAI API error: {str(e)}")
    
    async def generate_full_article(
        self,
        outline: ArticleOutline,
        target_keyword: str,
    ) -> str:
        """
        Generate complete article from outline.
        
        Args:
            outline: Complete article outline
            target_keyword: Main SEO keyword
            
        Returns:
            Full article in Markdown format
        """
        client = self._get_client()
        
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

        user_prompt = f"""請根據以下大綱生成一篇完整的 SEO 文章：

目標關鍵字：{target_keyword}
Meta 描述：{outline.meta_description}
目標字數：{outline.estimated_word_count}

大綱：
{outline_text}

請直接輸出完整的 Markdown 格式文章，不需要任何額外說明。"""

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=4000,
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            raise ExternalServiceException(f"OpenAI API error: {str(e)}")
    
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
        client = self._get_client()
        
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
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.5,
            )
            
            return response.choices[0].message.content or content
            
        except Exception as e:
            raise ExternalServiceException(f"OpenAI API error: {str(e)}")


# Singleton instance
llm_service = LLMService()
