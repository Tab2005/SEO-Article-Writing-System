"""
Google Custom Search API Service

This service handles interaction with Google Custom Search JSON API to:
- Perform keyword research and analysis  
- Extract SERP (Search Engine Results Pages) data
- Analyze competitor content and rankings
- Cache search results for efficiency
"""

import httpx
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus

from app.config import settings
from app.models.search_cache import SearchCache
from app.database import get_db

class GoogleSearchService:
    """Google Custom Search API service for SEO research."""
    
    def __init__(self):
        self.api_key = settings.google_api_key
        self.search_engine_id = settings.google_search_engine_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.client = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
            
    def _validate_config(self) -> bool:
        """Validate Google API configuration."""
        if not self.api_key or self.api_key == "your-google-api-key":
            return False
        if not self.search_engine_id or self.search_engine_id == "your-search-engine-id":
            return False
        return True
        
    async def _check_cache(self, query: str, language: str = "zh-TW", 
                          country: str = "TW", num_results: int = 10,
                          user_id: str = None, project_id: str = None) -> Optional[SearchCache]:
        """Check if search results exist in cache and are still valid."""
        cache_key = SearchCache.generate_cache_key(
            query, language, country, "web", num_results
        )
        
        async for db in get_db():
            try:
                from sqlalchemy import select
                
                # Find cached result
                result = await db.execute(
                    select(SearchCache).where(
                        SearchCache.cache_key == cache_key,
                        SearchCache.expires_at > datetime.utcnow()
                    )
                )
                cached_entry = result.scalar_one_or_none()
                
                if cached_entry:
                    # Update hit count and access time
                    cached_entry.increment_hit_count()
                    await db.commit()
                    return cached_entry
                    
            except Exception as e:
                print(f"Cache check error: {e}")
                await db.rollback()
                
        return None
        
    async def _save_to_cache(self, query: str, results: dict, user_id: str,
                           project_id: str = None, language: str = "zh-TW", 
                           country: str = "TW", num_results: int = 10,
                           search_time: float = 0.0) -> SearchCache:
        """Save search results to cache."""
        cache_entry = SearchCache.create_cache_entry(
            query=query,
            results=results,
            user_id=user_id,
            project_id=project_id,
            language=language,
            country=country,
            search_type="web",
            num_results=num_results,
            cache_hours=24  # Cache for 24 hours
        )
        
        cache_entry.search_time = search_time
        
        async for db in get_db():
            try:
                db.add(cache_entry)
                await db.commit()
                await db.refresh(cache_entry)
                return cache_entry
            except Exception as e:
                print(f"Cache save error: {e}")
                await db.rollback()
                raise e
                
        return cache_entry
        
    async def search(self, query: str, language: str = "zh-TW", 
                    country: str = "TW", num_results: int = 10,
                    start_index: int = 1, user_id: str = None,
                    project_id: str = None, use_cache: bool = True) -> Dict:
        """
        Perform Google Custom Search with caching.
        
        Args:
            query: Search query string
            language: Language code (zh-TW, en, etc.)
            country: Country code (TW, US, etc.)
            num_results: Number of results to return (max 10 per request)
            start_index: Starting index for pagination
            user_id: User ID for cache association
            project_id: Project ID for cache association
            use_cache: Whether to use/save cache
            
        Returns:
            Dictionary with search results and metadata
        """
        if not self._validate_config():
            raise ValueError("Google API key and Search Engine ID must be configured")
            
        # Check cache first if enabled
        if use_cache and user_id:
            cached_result = await self._check_cache(
                query, language, country, num_results, user_id, project_id
            )
            if cached_result:
                print(f"🎯 Cache hit for query: {query}")
                return {
                    "cached": True,
                    "cache_id": cached_result.id,
                    "results": cached_result.results,
                    "organic_results": cached_result.organic_results,
                    "serp_features": cached_result.serp_features,
                    "analysis": cached_result.analysis_data,
                    "search_time": cached_result.search_time,
                    "hit_count": cached_result.hit_count
                }
        
        # Build search parameters
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(num_results, 10),  # Google API max is 10
            "start": start_index,
            "lr": f"lang_{language.split('-')[0]}",  # Language restriction
            "gl": country.lower(),  # Geographic location
            "safe": "active",  # Safe search
            "fields": "items(title,link,snippet,displayLink,pagemap),searchInformation"
        }
        
        try:
            start_time = datetime.now()
            
            print(f"🔍 Searching Google for: {query} (lang: {language}, country: {country})")
            
            # Make API request
            response = await self.client.get(self.base_url, params=params)
            search_duration = (datetime.now() - start_time).total_seconds()
            
            response.raise_for_status()
            data = response.json()
            
            # Process and enhance results
            processed_results = await self._process_search_results(data, query)
            
            result = {
                "cached": False,
                "query": query,
                "language": language,
                "country": country,
                "results": data,
                "organic_results": processed_results.get("organic_results", []),
                "serp_features": processed_results.get("serp_features", {}),
                "search_time": search_duration,
                "total_results": int(data.get("searchInformation", {}).get("totalResults", 0)),
                "search_information": data.get("searchInformation", {})
            }
            
            # Save to cache if enabled
            if use_cache and user_id:
                try:
                    cache_entry = await self._save_to_cache(
                        query, data, user_id, project_id, 
                        language, country, num_results, search_duration
                    )
                    result["cache_id"] = cache_entry.id
                    print(f"💾 Results cached with ID: {cache_entry.id}")
                except Exception as e:
                    print(f"⚠️  Cache save failed: {e}")
                    
            return result
            
        except httpx.HTTPStatusError as e:
            error_detail = f"Google API Error {e.response.status_code}: {e.response.text}"
            print(f"❌ {error_detail}")
            raise Exception(error_detail)
        except Exception as e:
            print(f"❌ Search failed: {e}")
            raise e
            
    async def _process_search_results(self, data: dict, query: str) -> Dict:
        """Process raw Google search results into structured format."""
        processed = {
            "organic_results": [],
            "serp_features": {
                "total_results": 0,
                "search_time": 0.0,
                "featured_snippet": False,
                "knowledge_panel": False,
                "people_also_ask": False,
                "related_searches": False,
                "ads_detected": False
            }
        }
        
        # Extract organic results
        items = data.get("items", [])
        for idx, item in enumerate(items):
            organic_result = {
                "position": idx + 1,
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "display_link": item.get("displayLink", ""),
                "snippet": item.get("snippet", ""),
                "pagemap": item.get("pagemap", {})
            }
            
            # Enhanced metadata extraction
            pagemap = item.get("pagemap", {})
            if "metatags" in pagemap and pagemap["metatags"]:
                meta = pagemap["metatags"][0]
                organic_result.update({
                    "meta_description": meta.get("og:description", meta.get("description", "")),
                    "meta_title": meta.get("og:title", meta.get("title", "")),
                    "og_image": meta.get("og:image", ""),
                    "author": meta.get("author", ""),
                    "published_date": meta.get("article:published_time", "")
                })
                
            processed["organic_results"].append(organic_result)
            
        # Extract search information
        search_info = data.get("searchInformation", {})
        processed["serp_features"].update({
            "total_results": int(search_info.get("totalResults", 0)),
            "search_time": float(search_info.get("searchTime", 0.0))
        })
        
        return processed
        
    async def keyword_research(self, seed_keyword: str, language: str = "zh-TW",
                             country: str = "TW", user_id: str = None,
                             project_id: str = None) -> Dict:
        """
        Perform comprehensive keyword research.
        
        Args:
            seed_keyword: Main keyword to research
            language: Target language
            country: Target country
            user_id: User ID for tracking
            project_id: Project ID for association
            
        Returns:
            Dictionary with keyword analysis and related terms
        """
        print(f"🔬 Starting keyword research for: {seed_keyword}")
        
        results = {
            "seed_keyword": seed_keyword,
            "language": language,
            "country": country,
            "main_results": None,
            "related_queries": [],
            "competitor_analysis": {},
            "serp_analysis": {},
            "recommendations": []
        }
        
        try:
            # 1. Main keyword search
            main_search = await self.search(
                seed_keyword, language, country, 10, 1, user_id, project_id
            )
            results["main_results"] = main_search
            
            # 2. Generate related query variations
            query_variations = self._generate_keyword_variations(seed_keyword)
            
            # 3. Search for related keywords (limited to avoid API quota)
            for variation in query_variations[:3]:  # Limit to 3 variations
                try:
                    var_results = await self.search(
                        variation, language, country, 5, 1, user_id, project_id
                    )
                    results["related_queries"].append({
                        "query": variation,
                        "results": var_results
                    })
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"⚠️  Failed to search variation '{variation}': {e}")
                    
            # 4. Analyze competitors from main results
            if main_search.get("organic_results"):
                results["competitor_analysis"] = self._analyze_competitors(
                    main_search["organic_results"], seed_keyword
                )
                
            # 5. SERP feature analysis
            results["serp_analysis"] = self._analyze_serp_features(main_search)
            
            # 6. Generate recommendations
            results["recommendations"] = self._generate_keyword_recommendations(
                results, seed_keyword
            )
            
            print(f"✅ Keyword research completed for: {seed_keyword}")
            return results
            
        except Exception as e:
            print(f"❌ Keyword research failed for '{seed_keyword}': {e}")
            raise e
            
    def _generate_keyword_variations(self, seed_keyword: str) -> List[str]:
        """Generate keyword variations for research."""
        variations = []
        
        # Common Chinese/English modifiers and question patterns
        modifiers = [
            f"{seed_keyword} 教學",
            f"{seed_keyword} 推薦", 
            f"{seed_keyword} 比較",
            f"如何 {seed_keyword}",
            f"{seed_keyword} 技巧",
            f"{seed_keyword} 工具"
        ]
        
        # Add English variations if appropriate
        if any(char.isascii() for char in seed_keyword):
            english_modifiers = [
                f"{seed_keyword} tutorial",
                f"{seed_keyword} guide", 
                f"{seed_keyword} tips",
                f"how to {seed_keyword}",
                f"{seed_keyword} tools"
            ]
            variations.extend(english_modifiers)
            
        variations.extend(modifiers)
        return variations[:6]  # Limit variations
        
    def _analyze_competitors(self, organic_results: List[Dict], 
                           seed_keyword: str) -> Dict:
        """Analyze competitor information from search results."""
        competitors = {}
        domains_seen = set()
        
        for result in organic_results[:10]:
            domain = result.get("display_link", "").lower()
            if domain and domain not in domains_seen:
                domains_seen.add(domain)
                
                competitors[domain] = {
                    "domain": domain,
                    "title": result.get("title", ""),
                    "url": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "position": result.get("position", 0),
                    "meta_description": result.get("meta_description", ""),
                    "keyword_in_title": seed_keyword.lower() in result.get("title", "").lower(),
                    "keyword_in_snippet": seed_keyword.lower() in result.get("snippet", "").lower()
                }
                
        return {
            "total_competitors": len(competitors),
            "top_domains": list(competitors.keys())[:5],
            "competitor_details": competitors
        }
        
    def _analyze_serp_features(self, search_results: Dict) -> Dict:
        """Analyze SERP features and search landscape."""
        analysis = {
            "competition_level": "unknown",
            "serp_features_present": [],
            "content_gaps": [],
            "optimization_opportunities": []
        }
        
        organic_results = search_results.get("organic_results", [])
        total_results = search_results.get("total_results", 0)
        
        # Determine competition level based on total results and content quality
        if total_results > 1000000:
            analysis["competition_level"] = "high"
        elif total_results > 100000:
            analysis["competition_level"] = "medium" 
        else:
            analysis["competition_level"] = "low"
            
        # Analyze content patterns
        titles = [r.get("title", "") for r in organic_results]
        snippets = [r.get("snippet", "") for r in organic_results]
        
        # Look for content gaps and opportunities
        common_terms = self._extract_common_terms(titles + snippets)
        analysis["common_terms"] = common_terms
        
        return analysis
        
    def _extract_common_terms(self, texts: List[str]) -> List[str]:
        """Extract common terms from text list for content analysis."""
        # Simple term extraction - can be enhanced with NLP
        from collections import Counter
        import re
        
        all_words = []
        for text in texts:
            # Extract Chinese characters and English words
            chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)
            english_words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            all_words.extend(chinese_chars)
            all_words.extend(english_words)
            
        # Get most common terms
        counter = Counter(all_words)
        return [term for term, count in counter.most_common(10) if count > 1]
        
    def _generate_keyword_recommendations(self, research_data: Dict, 
                                        seed_keyword: str) -> List[Dict]:
        """Generate actionable keyword recommendations."""
        recommendations = []
        
        main_results = research_data.get("main_results", {})
        competition_level = research_data.get("serp_analysis", {}).get("competition_level", "unknown")
        
        # Recommendation 1: Competition analysis
        recommendations.append({
            "type": "competition_analysis",
            "title": f"'{seed_keyword}' 競爭分析",
            "description": f"競爭程度：{competition_level}",
            "action": "分析前10名競爭對手的內容策略",
            "priority": "high" if competition_level == "high" else "medium"
        })
        
        # Recommendation 2: Long-tail opportunities  
        related_queries = research_data.get("related_queries", [])
        if related_queries:
            recommendations.append({
                "type": "longtail_keywords",
                "title": "長尾關鍵字機會",
                "description": f"發現 {len(related_queries)} 個相關搜尋詞",
                "action": "優化長尾關鍵字內容",
                "priority": "medium"
            })
            
        # Recommendation 3: Content gaps
        common_terms = research_data.get("serp_analysis", {}).get("common_terms", [])
        if common_terms:
            recommendations.append({
                "type": "content_optimization", 
                "title": "內容優化建議",
                "description": f"常見相關詞彙：{', '.join(common_terms[:5])}",
                "action": "在內容中整合相關詞彙",
                "priority": "medium"
            })
            
        return recommendations

# Service instance for dependency injection
google_search_service = GoogleSearchService()