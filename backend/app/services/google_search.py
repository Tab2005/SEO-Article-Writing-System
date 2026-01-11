"""
Google Search Service.

Handles Google Custom Search API integration for SERP fetching.
"""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, List

import httpx

from app.config import settings
from app.core.exceptions import ExternalServiceException, BadRequestException
from app.schemas.research import SerpResult, SerpResponse
from app.services.runtime_settings import get_google_search_config


class GoogleSearchService:
    """Service for Google Custom Search API integration."""
    
    BASE_URL = "https://www.googleapis.com/customsearch/v1"
    
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    @staticmethod
    def _validate_config(api_key: Optional[str], cx_id: Optional[str]) -> None:
        """Validate API configuration."""
        if not api_key or not cx_id:
            raise BadRequestException(
                "Google Search API not configured. "
                "Please set GOOGLE_API_KEY and GOOGLE_CX_ID environment variables."
            )
    
    @staticmethod
    def generate_cache_key(keyword: str, market: str) -> str:
        """Generate cache key for keyword search."""
        key_string = f"{keyword.lower().strip()}:{market.lower()}"
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]
    
    async def search(
        self,
        keyword: str,
        market: str = "tw",
        num_results: int = 10,
        start_index: int = 1,
    ) -> SerpResponse:
        """
        Perform Google Custom Search.
        
        Args:
            keyword: Search keyword
            market: Target market (country code)
            num_results: Number of results to fetch (max 10 per request)
            start_index: Starting index for pagination
            
        Returns:
            SerpResponse with search results
        """
        api_key, cx_id = await get_google_search_config()
        self._validate_config(api_key, cx_id)
        
        # Map market to Google search parameters
        market_config = {
            "tw": {"gl": "tw", "hl": "zh-TW"},
            "us": {"gl": "us", "hl": "en"},
            "jp": {"gl": "jp", "hl": "ja"},
            "hk": {"gl": "hk", "hl": "zh-HK"},
        }
        
        config = market_config.get(market.lower(), market_config["tw"])
        
        params = {
            "key": api_key,
            "cx": cx_id,
            "q": keyword,
            "num": min(num_results, 10),  # API limit is 10
            "start": start_index,
            **config,
        }
        
        try:
            client = await self._get_client()
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise ExternalServiceException("Google API rate limit exceeded")
            raise ExternalServiceException(f"Google API error: {e.response.text}")
        except httpx.RequestError as e:
            raise ExternalServiceException(f"Network error: {str(e)}")
        
        # Parse results
        results: List[SerpResult] = []
        items = data.get("items", [])
        
        for rank, item in enumerate(items, start=start_index):
            results.append(
                SerpResult(
                    rank=rank,
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    scraped_at=datetime.now(timezone.utc),
                )
            )
        
        return SerpResponse(
            keyword=keyword,
            market=market,
            total_results=int(data.get("searchInformation", {}).get("totalResults", 0)),
            results=results,
            cached=False,
            fetched_at=datetime.now(timezone.utc),
        )
    
    async def search_all(
        self,
        keyword: str,
        market: str = "tw",
        max_results: int = 10,
    ) -> SerpResponse:
        """
        Fetch all results up to max_results with pagination.
        
        Args:
            keyword: Search keyword
            market: Target market
            max_results: Maximum results to fetch (max 100)
            
        Returns:
            Combined SerpResponse with all results
        """
        max_results = min(max_results, 100)  # API limit
        all_results: List[SerpResult] = []
        total_results = 0
        
        for start in range(1, max_results + 1, 10):
            num_to_fetch = min(10, max_results - len(all_results))
            if num_to_fetch <= 0:
                break
            
            response = await self.search(
                keyword=keyword,
                market=market,
                num_results=num_to_fetch,
                start_index=start,
            )
            
            if not response.results:
                break
            
            all_results.extend(response.results)
            total_results = response.total_results
        
        return SerpResponse(
            keyword=keyword,
            market=market,
            total_results=total_results,
            results=all_results,
            cached=False,
            fetched_at=datetime.now(timezone.utc),
        )


# Singleton instance
google_search_service = GoogleSearchService()
