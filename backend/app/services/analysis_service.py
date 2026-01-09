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
)


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
        """Extract most common headings across competitors."""
        headings: List[str] = []
        
        for competitor in competitors:
            if heading_type == "h2":
                headings.extend(competitor.headings.h2)
            elif heading_type == "h3":
                headings.extend(competitor.headings.h3)
            elif heading_type == "h1":
                headings.extend(competitor.headings.h1)
        
        # Normalize and count
        normalized = [h.strip().lower() for h in headings if h.strip()]
        counter = Counter(normalized)
        
        # Return original case of most common ones
        common = [h for h, _ in counter.most_common(top_n)]
        
        return common
    
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
        
        return AnalysisReport(
            keyword=keyword,
            market=market,
            avg_word_count=word_stats["avg"],
            min_word_count=word_stats["min"],
            max_word_count=word_stats["max"],
            common_h2_tags=common_h2,
            common_h3_tags=common_h3,
            keyword_frequency=keyword_freq,
            competitor_count=len(competitors),
            competitors=competitors,
            generated_at=datetime.now(timezone.utc),
        )


# Singleton instance
analysis_service = AnalysisService()
