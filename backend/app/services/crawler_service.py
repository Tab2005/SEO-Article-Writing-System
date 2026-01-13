"""
Web Crawler Service.

Handles async web page crawling for competitor analysis.
"""

import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.exceptions import ExternalServiceException
from app.schemas.research import CompetitorData, HeadingStructure


class CrawlerService:
    """Service for crawling and analyzing competitor pages."""
    
    # Common user agents for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]
    
    # Domains to skip (login walls, paywalls, etc.)
    BLOCKED_DOMAINS = [
        "facebook.com",
        "instagram.com",
        "twitter.com",
        "x.com",
        "linkedin.com",
    ]
    
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._user_agent_index = 0
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=15.0,
                follow_redirects=True,
                headers={"User-Agent": self._get_user_agent()},
            )
        return self._client
    
    def _get_user_agent(self) -> str:
        """Get rotating user agent."""
        ua = self.USER_AGENTS[self._user_agent_index % len(self.USER_AGENTS)]
        self._user_agent_index += 1
        return ua
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    def _is_blocked_domain(self, url: str) -> bool:
        """Check if domain should be skipped."""
        try:
            domain = urlparse(url).netloc.lower()
            return any(blocked in domain for blocked in self.BLOCKED_DOMAINS)
        except Exception:
            return True
    
    @staticmethod
    def _extract_text(soup: BeautifulSoup) -> str:
        """Extract main text content from page."""
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
            element.decompose()
        
        # Get text
        text = soup.get_text(separator=" ", strip=True)
        
        # Clean up whitespace
        text = re.sub(r"\s+", " ", text)
        
        return text
    
    @staticmethod
    def _count_words(text: str) -> int:
        """Count words in text (handles CJK characters)."""
        # For CJK languages, count characters as words
        cjk_pattern = re.compile(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]")
        cjk_count = len(cjk_pattern.findall(text))
        
        # For non-CJK, count word boundaries
        non_cjk_text = cjk_pattern.sub(" ", text)
        word_count = len(non_cjk_text.split())
        
        return cjk_count + word_count
    
    @staticmethod
    def _extract_headings(soup: BeautifulSoup) -> HeadingStructure:
        """Extract heading structure from page."""
        return HeadingStructure(
            h1=[h.get_text(strip=True) for h in soup.find_all("h1")[:5]],
            h2=[h.get_text(strip=True) for h in soup.find_all("h2")[:10]],
            h3=[h.get_text(strip=True) for h in soup.find_all("h3")[:15]],
        )
    
    @staticmethod
    def _extract_meta(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        """Extract meta tags from page."""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        
        return {
            "description": meta_desc.get("content") if meta_desc else None,
            "keywords": meta_keywords.get("content") if meta_keywords else None,
        }
    
    async def crawl_page(
        self,
        url: str,
        rank: int = 0,
    ) -> Optional[CompetitorData]:
        """
        Crawl a single page and extract SEO data.
        
        Args:
            url: Page URL to crawl
            rank: SERP rank of the page
            
        Returns:
            CompetitorData or None if crawling failed
        """
        if self._is_blocked_domain(url):
            return None
        
        try:
            client = await self._get_client()
            response = await client.get(
                url,
                headers={"User-Agent": self._get_user_agent()},
            )
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "lxml")
            
            # Extract data
            title = soup.title.string if soup.title else ""
            text = self._extract_text(soup)
            # Prevent unbounded payload size
            if len(text) > 200_000:
                text = text[:200_000]
            word_count = self._count_words(text)
            headings = self._extract_headings(soup)
            meta = self._extract_meta(soup)
            
            return CompetitorData(
                rank=rank,
                url=url,
                title=title.strip() if title else "",
                word_count=word_count,
                headings=headings,
                meta_description=meta.get("description"),
                meta_keywords=meta.get("keywords"),
                content_text=text,
                scraped_at=datetime.now(timezone.utc),
            )
            
        except httpx.HTTPStatusError as e:
            # Log but don't fail - some pages may be unavailable
            return None
        except httpx.RequestError:
            return None
        except Exception:
            return None
    
    async def crawl_pages(
        self,
        urls: List[str],
    ) -> List[CompetitorData]:
        """
        Crawl multiple pages concurrently.
        
        Args:
            urls: List of URLs to crawl
            
        Returns:
            List of CompetitorData for successfully crawled pages
        """
        # Return mock data for development
        import asyncio
        
        mock_data = []
        for rank, url in enumerate(urls, start=1):
            mock_data.append(self._get_mock_competitor_data(url, rank))
        
        return mock_data
    
    def _get_mock_competitor_data(self, url: str, rank: int) -> CompetitorData:
        """Return mock competitor data for development."""
        from datetime import datetime, timezone
        
        return CompetitorData(
            rank=rank,
            url=url,
            title=f"Mock Title for {url}",
            word_count=1500 + rank * 100,
            headings=HeadingStructure(
                h1=["Mock H1"],
                h2=["Mock H2 Section", "Another H2"],
                h3=["Mock H3 Subsection"]
            ),
            meta_description=f"Mock description for {url}",
            meta_keywords="mock, keywords, test",
            content_text="Mock content text for SEO analysis. This is a placeholder for actual crawled content.",
            scraped_at=datetime.now(timezone.utc),
        )


# Singleton instance
crawler_service = CrawlerService()
