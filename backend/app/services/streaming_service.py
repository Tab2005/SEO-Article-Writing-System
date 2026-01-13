"""
Streaming Service.

Provides Server-Sent Events (SSE) streaming for content generation.
"""

import asyncio
import json
from typing import AsyncGenerator, Optional, List, Dict, Any

from app.services.llm_service import llm_service
from app.schemas.article import ArticleOutline, OutlineSection


class StreamingService:
    """
    Service for streaming content generation via SSE.
    
    Generates content section by section and streams progress events.
    """
    
    async def stream_article_content(
        self,
        outline: ArticleOutline,
        target_keyword: str,
        secondary_keywords: Optional[List[str]] = None,
        tone: str = "professional",
    ) -> AsyncGenerator[str, None]:
        """
        Stream article content generation via SSE.
        
        Yields SSE-formatted events for:
        - progress: Current section being generated
        - content: Generated section content
        - done: Generation complete with stats
        
        Args:
            outline: Article outline to expand
            target_keyword: Main keyword
            secondary_keywords: Additional keywords
            tone: Writing tone
            
        Yields:
            SSE-formatted event strings
        """
        sections = outline.sections
        total_sections = len(sections)
        generated_content: List[str] = []
        total_words = 0
        
        # Generate title
        yield self._format_sse_event("progress", {
            "section": "標題",
            "current": 0,
            "total": total_sections,
            "progress": 0,
        })
        
        # Start with the main title
        title_content = f"# {outline.title}\n\n"
        if outline.meta_description:
            title_content += f"> {outline.meta_description}\n\n"
        
        generated_content.append(title_content)
        total_words += len(title_content.split())
        
        yield self._format_sse_event("content", {
            "section": "標題",
            "content": title_content,
        })
        
        # Generate each section
        for idx, section in enumerate(sections):
            progress = int(((idx + 1) / total_sections) * 100)
            
            # Send progress event
            yield self._format_sse_event("progress", {
                "section": section.heading,
                "current": idx + 1,
                "total": total_sections,
                "progress": progress,
            })
            
            # Generate section content
            try:
                section_content = await self._generate_section_content(
                    section=section,
                    target_keyword=target_keyword,
                    secondary_keywords=secondary_keywords,
                    tone=tone,
                    context=f"Article title: {outline.title}",
                )
            except Exception as e:
                section_content = f"## {section.heading}\n\n（生成失敗：{str(e)}）\n\n"
            
            generated_content.append(section_content)
            section_words = len(section_content.split())
            total_words += section_words
            
            # Send content event
            yield self._format_sse_event("content", {
                "section": section.heading,
                "content": section_content,
                "words": section_words,
            })
            
            # Small delay to prevent overwhelming the client
            await asyncio.sleep(0.1)
        
        # Send completion event
        full_content = "\n".join(generated_content)
        yield self._format_sse_event("done", {
            "total_words": total_words,
            "total_sections": total_sections,
            "content": full_content,
        })
    
    async def _generate_section_content(
        self,
        section: OutlineSection,
        target_keyword: str,
        secondary_keywords: Optional[List[str]],
        tone: str,
        context: str,
    ) -> str:
        """
        Generate content for a single section using LLM.
        
        Args:
            section: Section to generate
            target_keyword: Main keyword
            secondary_keywords: Additional keywords
            tone: Writing tone
            context: Additional context
            
        Returns:
            Generated markdown content
        """
        # Use the existing LLM service method
        content = await llm_service.generate_section_content(
            section=section,
            context=context,
            target_keyword=target_keyword,
        )
        
        return content
    
    def _format_sse_event(self, event_type: str, data: Dict[str, Any]) -> str:
        """
        Format data as an SSE event.
        
        Args:
            event_type: Event name (progress, content, done, error)
            data: Event data dictionary
            
        Returns:
            SSE-formatted string
        """
        return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
    
    async def stream_section_by_section(
        self,
        sections: List[Dict[str, Any]],
        target_keyword: str,
        tone: str = "professional",
    ) -> AsyncGenerator[str, None]:
        """
        Simplified streaming that generates content section by section.
        
        For use when you already have a list of section dictionaries.
        """
        total = len(sections)
        all_content = []
        
        for idx, section_data in enumerate(sections):
            heading = section_data.get("heading", f"Section {idx + 1}")
            key_points = section_data.get("key_points", [])
            
            progress = int(((idx + 1) / total) * 100)
            
            yield self._format_sse_event("progress", {
                "section": heading,
                "current": idx + 1,
                "total": total,
                "progress": progress,
            })
            
            # Generate simple content based on heading and key points
            content = f"## {heading}\n\n"
            for point in key_points:
                content += f"- {point}\n"
            content += "\n"
            
            all_content.append(content)
            
            yield self._format_sse_event("content", {
                "section": heading,
                "content": content,
            })
            
            await asyncio.sleep(0.5)  # Simulate generation time
        
        full_content = "\n".join(all_content)
        yield self._format_sse_event("done", {
            "total_words": len(full_content.split()),
            "content": full_content,
        })


# Singleton instance
streaming_service = StreamingService()
