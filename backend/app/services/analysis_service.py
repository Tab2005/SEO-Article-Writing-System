"""
Analysis Service.

Aggregates competitor data and generates SEO insights.
"""

from collections import Counter
from datetime import datetime, timezone
from typing import List, Dict, Optional

from app.schemas.research import (
    CompetitorData,
    AnalysisReport,
    SerpResponse,
    TFIDFAnalysis,
    KeywordItem,
    KeywordCount,
    KeywordCategories,
)
from app.services.tfidf_service import tfidf_service


class AnalysisService:
    """Service for analyzing competitor data and generating insights."""
    
    @staticmethod
    def calculate_word_stats(competitors: List[CompetitorData]) -> Dict[str, int]:
        """Calculate word count statistics."""
        if not competitors:
            return {"avg": 0, "min": 0, "max": 0}
        
        word_counts = [c.word_count for c in competitors]
        
        return {
            "avg": sum(word_counts) // len(word_counts),
            "min": min(word_counts),
            "max": max(word_counts),
        }
    
    @staticmethod
    def extract_common_headings(
        competitors: List[CompetitorData],
        heading_type: str = "h2",
        top_n: int = 10,
    ) -> List[str]:
        """
        Extract representative headings from all competitors.
        
        Uses a round-robin approach to fairly sample headings from each competitor,
        ensuring diversity rather than favoring one competitor.
        Also prioritizes truly common headings (appearing in multiple competitors).
        """
        if not competitors:
            return []
        
        # Collect headings grouped by competitor
        heading_by_competitor: List[List[str]] = []
        
        for competitor in competitors:
            if heading_type == "h2":
                headings = [h.strip() for h in competitor.headings.h2 if h.strip()]
            elif heading_type == "h3":
                headings = [h.strip() for h in competitor.headings.h3 if h.strip()]
            elif heading_type == "h1":
                headings = [h.strip() for h in competitor.headings.h1 if h.strip()]
            else:
                headings = []
            heading_by_competitor.append(headings)
        
        # First, find truly common headings (appear in 2+ competitors)
        heading_count: Dict[str, int] = Counter()
        heading_original: Dict[str, str] = {}
        
        for headings in heading_by_competitor:
            seen = set()
            for h in headings:
                normalized = h.lower()
                if normalized not in seen:
                    seen.add(normalized)
                    heading_count[normalized] += 1
                    if normalized not in heading_original:
                        heading_original[normalized] = h
        
        # Collect truly common headings first (count >= 2)
        common_headings = [
            heading_original[h] for h, count in 
            sorted(heading_count.items(), key=lambda x: -x[1])
            if count >= 2
        ]
        
        # If we have enough common headings, return them
        if len(common_headings) >= top_n:
            return common_headings[:top_n]
        
        # Otherwise, round-robin sample from each competitor to fill remaining slots
        result = list(common_headings)
        seen_normalized = {h.lower() for h in result}
        
        # Calculate how many headings to take from each competitor
        remaining = top_n - len(result)
        num_competitors = len([c for c in heading_by_competitor if c])
        if num_competitors == 0:
            return result
        
        # Round-robin: take one from each competitor until we have enough
        indices = [0] * len(heading_by_competitor)
        added = True
        while len(result) < top_n and added:
            added = False
            for i, headings in enumerate(heading_by_competitor):
                if len(result) >= top_n:
                    break
                while indices[i] < len(headings):
                    h = headings[indices[i]]
                    indices[i] += 1
                    if h.lower() not in seen_normalized:
                        result.append(h)
                        seen_normalized.add(h.lower())
                        added = True
                        break
        
        return result
    
    @staticmethod
    def calculate_keyword_frequency(
        competitors: List[CompetitorData],
        target_keyword: str,
    ) -> Dict[str, int]:
        """Calculate keyword frequency in titles and headings."""
        frequency: Dict[str, int] = {}
        keyword_lower = target_keyword.lower()
        
        for competitor in competitors:
            # Check title
            if keyword_lower in competitor.title.lower():
                frequency["title"] = frequency.get("title", 0) + 1
            
            # Check H1
            for h1 in competitor.headings.h1:
                if keyword_lower in h1.lower():
                    frequency["h1"] = frequency.get("h1", 0) + 1
            
            # Check H2
            for h2 in competitor.headings.h2:
                if keyword_lower in h2.lower():
                    frequency["h2"] = frequency.get("h2", 0) + 1
            
            # Check meta description
            if competitor.meta_description:
                if keyword_lower in competitor.meta_description.lower():
                    frequency["meta_description"] = frequency.get("meta_description", 0) + 1
        
        return frequency
    
    def extract_tfidf_keywords(
        self,
        competitors: List[CompetitorData],
        target_keyword: str,
        top_n: int = 30,
    ) -> Optional[TFIDFAnalysis]:
        """
        使用 TF-IDF 提取競品關鍵詞。
        
        Args:
            competitors: 競品資料列表
            target_keyword: 目標關鍵字
            top_n: 返回前 N 個關鍵詞
            
        Returns:
            TFIDFAnalysis 結果
        """
        try:
            result = tfidf_service.analyze_competitors(
                competitors=competitors,
                target_keyword=target_keyword,
                top_n=top_n,
            )
            
            return TFIDFAnalysis(
                suggested_keywords=[
                    KeywordItem(term=k["term"], score=k["score"])
                    for k in result["suggested_keywords"]
                ],
                keyword_categories=KeywordCategories(
                    high_frequency=[
                        KeywordItem(term=k["term"], score=k["score"])
                        for k in result["keyword_categories"]["high_frequency"]
                    ],
                    semantic_related=[
                        KeywordItem(term=k["term"], score=k["score"])
                        for k in result["keyword_categories"]["semantic_related"]
                    ],
                    long_tail=[
                        KeywordItem(term=k["term"], score=k["score"])
                        for k in result["keyword_categories"]["long_tail"]
                    ],
                ),
                competitor_common_terms=[
                    KeywordCount(term=k["term"], count=k["count"])
                    for k in result["competitor_common_terms"]
                ],
            )
        except Exception as e:
            print(f"[TF-IDF] Analysis failed: {e}")
            return None
    
    def generate_report(
        self,
        keyword: str,
        market: str,
        competitors: List[CompetitorData],
    ) -> AnalysisReport:
        """
        Generate comprehensive analysis report.
        
        Args:
            keyword: Target keyword
            market: Target market
            competitors: List of analyzed competitor data
            
        Returns:
            AnalysisReport with all insights
        """
        word_stats = self.calculate_word_stats(competitors)
        common_h2 = self.extract_common_headings(competitors, "h2", 10)
        common_h3 = self.extract_common_headings(competitors, "h3", 10)
        keyword_freq = self.calculate_keyword_frequency(competitors, keyword)
        
        # TF-IDF 關鍵詞分析
        tfidf_analysis = self.extract_tfidf_keywords(competitors, keyword)
        
        return AnalysisReport(
            keyword=keyword,
            market=market,
            avg_word_count=word_stats["avg"],
            min_word_count=word_stats["min"],
            max_word_count=word_stats["max"],
            common_h2_tags=common_h2,
            common_h3_tags=common_h3,
            keyword_frequency=keyword_freq,
            tfidf_analysis=tfidf_analysis,
            competitor_count=len(competitors),
            competitors=competitors,
            generated_at=datetime.now(timezone.utc),
        )


# Singleton instance
analysis_service = AnalysisService()
