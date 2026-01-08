"""
OpenAI API Integration Service

This module provides a comprehensive interface to OpenAI's GPT models for content generation.
Features include:
- Article outline generation based on SEO research
- Full article content generation with SEO optimization
- Content refinement and optimization
- Token usage tracking and cost management
- Rate limiting and error handling
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager
import json
import re
from datetime import datetime, timedelta

import openai
import tiktoken
from openai import AsyncOpenAI
from structlog import get_logger

from app.config import settings

logger = get_logger()

class ContentType:
    """Content generation types."""
    OUTLINE = "outline"
    ARTICLE = "article"
    SECTION = "section"
    TITLE = "title"
    META_DESCRIPTION = "meta_description"
    SUMMARY = "summary"

class OpenAIService:
    """OpenAI API service for content generation."""
    
    def __init__(self):
        self.client: Optional[AsyncOpenAI] = None
        self.model = settings.openai_model
        self.max_tokens = settings.openai_max_tokens
        self.temperature = settings.openai_temperature
        self.requests_per_minute = settings.openai_requests_per_minute
        
        # Rate limiting
        self._request_timestamps = []
        self._last_cleanup = time.time()
        
        # Token counting
        try:
            self.tokenizer = tiktoken.encoding_for_model(self.model)
        except KeyError:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            
        # Usage tracking
        self.usage_stats = {
            "requests": 0,
            "tokens_used": 0,
            "cost_estimate": 0.0,
            "errors": 0
        }
        
    async def __aenter__(self):
        """Async context manager entry."""
        if not self.client:
            await self._initialize_client()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.close()
            self.client = None
            
    async def _initialize_client(self):
        """Initialize OpenAI client."""
        if not settings.openai_api_key or settings.openai_api_key == "":
            logger.warning("OpenAI API key not configured")
            return False
            
        try:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info("OpenAI client initialized", model=self.model)
            return True
        except Exception as e:
            logger.error("Failed to initialize OpenAI client", error=str(e))
            return False
            
    def _validate_config(self) -> bool:
        """Validate OpenAI configuration."""
        return bool(settings.openai_api_key and settings.openai_api_key != "")
        
    async def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        current_time = time.time()
        
        # Clean up old timestamps (older than 1 minute)
        if current_time - self._last_cleanup > 60:
            cutoff_time = current_time - 60
            self._request_timestamps = [
                ts for ts in self._request_timestamps if ts > cutoff_time
            ]
            self._last_cleanup = current_time
            
        # Check if we're within rate limit
        if len(self._request_timestamps) >= self.requests_per_minute:
            wait_time = 60 - (current_time - self._request_timestamps[0])
            if wait_time > 0:
                logger.warning(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
                
        # Add current request timestamp
        self._request_timestamps.append(current_time)
        
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed: {e}")
            return len(text.split()) * 1.3  # Rough estimate
            
    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate API cost based on token usage."""
        # GPT-4o-mini pricing (as of 2024)
        input_cost_per_1k = 0.00015  # $0.00015 per 1K input tokens
        output_cost_per_1k = 0.0006  # $0.0006 per 1K output tokens
        
        input_cost = (prompt_tokens / 1000) * input_cost_per_1k
        output_cost = (completion_tokens / 1000) * output_cost_per_1k
        
        return input_cost + output_cost
        
    async def _make_request(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Make a request to OpenAI API with error handling."""
        if not self.client:
            if not await self._initialize_client():
                return None
                
        # Check rate limits
        await self._check_rate_limit()
        
        try:
            # Count input tokens
            prompt_text = "\n".join(msg["content"] for msg in messages)
            prompt_tokens = self._count_tokens(prompt_text)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature
            )
            
            # Extract response data
            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content
                completion_tokens = self._count_tokens(content or "")
                
                # Update usage statistics
                self.usage_stats["requests"] += 1
                self.usage_stats["tokens_used"] += prompt_tokens + completion_tokens
                cost = self._estimate_cost(prompt_tokens, completion_tokens)
                self.usage_stats["cost_estimate"] += cost
                
                logger.info(
                    "OpenAI request successful",
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cost_usd=cost
                )
                
                return {
                    "content": content,
                    "usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens,
                        "cost_estimate": cost
                    }
                }
                
        except openai.RateLimitError as e:
            logger.warning("OpenAI rate limit exceeded", error=str(e))
            self.usage_stats["errors"] += 1
            await asyncio.sleep(60)  # Wait 1 minute on rate limit
            return None
            
        except openai.APIError as e:
            logger.error("OpenAI API error", error=str(e))
            self.usage_stats["errors"] += 1
            return None
            
        except Exception as e:
            logger.error("Unexpected error in OpenAI request", error=str(e))
            self.usage_stats["errors"] += 1
            return None
            
        return None
        
    async def generate_outline(
        self,
        keyword: str,
        competitor_data: Optional[List[Dict]] = None,
        target_length: int = 2000,
        language: str = "zh-tw"
    ) -> Optional[Dict[str, Any]]:
        """
        Generate article outline based on keyword and competitor analysis.
        
        Args:
            keyword: Target keyword for the article
            competitor_data: Analysis of competing articles
            target_length: Target word count for the article
            language: Content language
            
        Returns:
            Dictionary with outline structure and metadata
        """
        try:
            # Prepare competitor context
            competitor_context = ""
            if competitor_data:
                competitor_titles = []
                competitor_headings = []
                for comp in competitor_data[:5]:  # Use top 5 competitors
                    competitor_titles.append(comp.get("title", ""))
                    if comp.get("headings"):
                        competitor_headings.extend(comp["headings"][:3])
                        
                competitor_context = f"""
競爭對手文章標題：
{chr(10).join(f"- {title}" for title in competitor_titles if title)}

常見標題結構：
{chr(10).join(f"- {heading}" for heading in competitor_headings[:10] if heading)}
"""

            system_prompt = f"""你是一位專業的 SEO 內容策劃師。請基於給定的關鍵字和競爭對手分析，生成一個優化的文章大綱。

要求：
1. 大綱應包含 H1、H2、H3 結構
2. 針對關鍵字「{keyword}」進行 SEO 優化
3. 目標字數約 {target_length} 字
4. 語言：{language}
5. 結構清晰，邏輯性強
6. 包含引言、主體內容和結論

輸出格式為 JSON：
{{
    "title": "文章標題",
    "meta_description": "meta 描述（150字以內）",
    "outline": [
        {{
            "level": 1,
            "heading": "H1 標題",
            "content_points": ["要點1", "要點2"]
        }},
        {{
            "level": 2,
            "heading": "H2 標題",
            "content_points": ["要點1", "要點2", "要點3"]
        }}
    ],
    "word_count_estimate": 2000,
    "seo_focus": ["主要關鍵字", "次要關鍵字"],
    "target_audience": "目標讀者描述"
}}"""

            user_prompt = f"""關鍵字：{keyword}

{competitor_context if competitor_context else "無競爭對手數據"}

請生成完整的文章大綱。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self._make_request(messages, max_tokens=2000, temperature=0.7)
            
            if response and response["content"]:
                try:
                    # Parse JSON response
                    outline_data = json.loads(response["content"])
                    
                    # Validate and structure the response
                    structured_outline = {
                        "title": outline_data.get("title", f"{keyword} - 完整指南"),
                        "meta_description": outline_data.get("meta_description", ""),
                        "outline": outline_data.get("outline", []),
                        "word_count_estimate": outline_data.get("word_count_estimate", target_length),
                        "seo_focus": outline_data.get("seo_focus", [keyword]),
                        "target_audience": outline_data.get("target_audience", "一般讀者"),
                        "generated_at": datetime.now().isoformat(),
                        "usage": response["usage"]
                    }
                    
                    logger.info("Outline generated successfully", keyword=keyword)
                    return structured_outline
                    
                except json.JSONDecodeError as e:
                    logger.error("Failed to parse outline JSON", error=str(e))
                    return None
                    
        except Exception as e:
            logger.error("Failed to generate outline", keyword=keyword, error=str(e))
            return None
            
        return None
        
    async def generate_article_section(
        self,
        heading: str,
        content_points: List[str],
        keyword: str,
        context: str = "",
        target_length: int = 300,
        language: str = "zh-tw"
    ) -> Optional[Dict[str, Any]]:
        """
        Generate content for a specific article section.
        
        Args:
            heading: Section heading
            content_points: Key points to cover
            keyword: Main keyword to optimize for
            context: Additional context from other sections
            target_length: Target word count for this section
            language: Content language
            
        Returns:
            Dictionary with generated content and metadata
        """
        try:
            system_prompt = f"""你是一位專業的 SEO 文案寫手。請基於給定的標題和要點，撰寫高品質的文章段落。

要求：
1. 圍繞關鍵字「{keyword}」進行 SEO 優化
2. 目標字數約 {target_length} 字
3. 語言：{language}
4. 內容要有價值、實用且易讀
5. 適當使用關鍵字但避免過度優化
6. 包含具體的建議和例子

格式要求：
- 使用 Markdown 格式
- 適當使用粗體 **重點** 和項目符號
- 段落間要有適當的空行"""

            points_text = "\n".join(f"- {point}" for point in content_points)
            
            user_prompt = f"""標題：{heading}

要點：
{points_text}

{f"上下文：{context}" if context else ""}

請撰寫這個段落的詳細內容。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self._make_request(messages, max_tokens=800, temperature=0.8)
            
            if response and response["content"]:
                return {
                    "heading": heading,
                    "content": response["content"],
                    "word_count": len(response["content"].split()),
                    "generated_at": datetime.now().isoformat(),
                    "usage": response["usage"]
                }
                
        except Exception as e:
            logger.error("Failed to generate article section", heading=heading, error=str(e))
            return None
            
        return None
        
    async def generate_full_article(
        self,
        outline: Dict[str, Any],
        keyword: str,
        language: str = "zh-tw"
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a complete article based on an outline.
        
        Args:
            outline: Article outline structure
            keyword: Main keyword
            language: Content language
            
        Returns:
            Dictionary with complete article and metadata
        """
        try:
            sections = []
            total_usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cost_estimate": 0.0
            }
            
            # Generate each section
            for section in outline.get("outline", []):
                heading = section.get("heading", "")
                content_points = section.get("content_points", [])
                level = section.get("level", 2)
                
                # Determine target length based on section level
                if level == 1:
                    target_length = 200  # Introduction
                elif level == 2:
                    target_length = 400  # Main sections
                else:
                    target_length = 250  # Subsections
                    
                section_result = await self.generate_article_section(
                    heading=heading,
                    content_points=content_points,
                    keyword=keyword,
                    target_length=target_length,
                    language=language
                )
                
                if section_result:
                    sections.append(section_result)
                    
                    # Accumulate usage statistics
                    usage = section_result.get("usage", {})
                    for key in total_usage:
                        total_usage[key] += usage.get(key, 0)
                        
                    # Small delay to avoid overwhelming the API
                    await asyncio.sleep(1)
                    
            # Combine all sections into a full article
            article_content = f"# {outline.get('title', '')}\n\n"
            
            for section in sections:
                # Determine heading level from original outline
                heading = section["heading"]
                content = section["content"]
                
                # Add section to article
                article_content += content + "\n\n"
                
            return {
                "title": outline.get("title", ""),
                "meta_description": outline.get("meta_description", ""),
                "content": article_content.strip(),
                "sections": sections,
                "word_count": sum(section["word_count"] for section in sections),
                "seo_focus": outline.get("seo_focus", []),
                "generated_at": datetime.now().isoformat(),
                "usage": total_usage
            }
            
        except Exception as e:
            logger.error("Failed to generate full article", error=str(e))
            return None
            
        return None
        
    async def optimize_content(
        self,
        content: str,
        keyword: str,
        optimization_type: str = "seo",
        language: str = "zh-tw"
    ) -> Optional[Dict[str, Any]]:
        """
        Optimize existing content for SEO or readability.
        
        Args:
            content: Original content to optimize
            keyword: Target keyword
            optimization_type: Type of optimization ("seo", "readability", "length")
            language: Content language
            
        Returns:
            Dictionary with optimized content and suggestions
        """
        try:
            if optimization_type == "seo":
                system_prompt = f"""你是一位 SEO 專家。請優化以下內容，提高其在搜索引擎中的排名表現。

優化重點：
1. 關鍵字「{keyword}」的自然融入
2. 改善標題結構和層次
3. 增加語義相關的詞彙
4. 優化內容可讀性
5. 添加有價值的資訊

請提供：
1. 優化後的內容
2. 具體的修改建議
3. SEO 評分改善點"""

            elif optimization_type == "readability":
                system_prompt = """你是一位內容編輯專家。請改善以下內容的可讀性和用戶體驗。

優化重點：
1. 簡化複雜句子
2. 增加段落間的邏輯連接
3. 使用更清晰的表達
4. 添加有用的例子或說明
5. 改善整體結構"""

            else:  # length optimization
                system_prompt = """你是一位內容編輯。請調整以下內容的長度，保持核心資訊的同時提高內容密度。"""

            user_prompt = f"""原始內容：
{content}

目標關鍵字：{keyword}

請提供優化建議和改善後的版本。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self._make_request(messages, max_tokens=3000, temperature=0.6)
            
            if response and response["content"]:
                return {
                    "original_content": content,
                    "optimized_content": response["content"],
                    "optimization_type": optimization_type,
                    "keyword": keyword,
                    "generated_at": datetime.now().isoformat(),
                    "usage": response["usage"]
                }
                
        except Exception as e:
            logger.error("Failed to optimize content", error=str(e))
            return None
            
        return None
        
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        return {
            **self.usage_stats,
            "model": self.model,
            "configured": self._validate_config(),
            "last_updated": datetime.now().isoformat()
        }
        
    def reset_usage_statistics(self):
        """Reset usage statistics."""
        self.usage_stats = {
            "requests": 0,
            "tokens_used": 0,
            "cost_estimate": 0.0,
            "errors": 0
        }

# Global OpenAI service instance
openai_service = OpenAIService()

@asynccontextmanager
async def get_openai_service():
    """Get OpenAI service instance with context management."""
    async with openai_service as service:
        yield service