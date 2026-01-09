"""
SEO Score Checker Service.

Analyzes article content and provides SEO scoring.
"""

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SEOCheckResult:
    """Result of a single SEO check."""
    name: str
    passed: bool
    score: int  # 0-100
    message: str
    recommendation: Optional[str] = None


@dataclass
class SEOReport:
    """Complete SEO analysis report."""
    overall_score: int
    checks: List[SEOCheckResult]
    summary: str


class SEOScoreChecker:
    """Service for checking SEO score of content."""
    
    def __init__(self):
        self.weights = {
            "title_keyword": 15,
            "meta_description": 10,
            "word_count": 15,
            "heading_structure": 15,
            "keyword_density": 15,
            "internal_links": 10,
            "readability": 10,
            "image_alt": 5,
            "url_structure": 5,
        }
    
    def check_title_keyword(
        self,
        title: str,
        keyword: str,
    ) -> SEOCheckResult:
        """Check if keyword is in title."""
        keyword_lower = keyword.lower()
        title_lower = title.lower()
        
        if keyword_lower in title_lower:
            # Check position
            position = title_lower.find(keyword_lower)
            if position < len(title) // 3:
                return SEOCheckResult(
                    name="標題關鍵字",
                    passed=True,
                    score=100,
                    message="關鍵字出現在標題前段，非常好！",
                )
            else:
                return SEOCheckResult(
                    name="標題關鍵字",
                    passed=True,
                    score=80,
                    message="標題包含關鍵字",
                    recommendation="建議將關鍵字移到標題前段",
                )
        else:
            return SEOCheckResult(
                name="標題關鍵字",
                passed=False,
                score=0,
                message="標題未包含目標關鍵字",
                recommendation="請在標題中加入目標關鍵字",
            )
    
    def check_meta_description(
        self,
        meta_description: str,
        keyword: str,
    ) -> SEOCheckResult:
        """Check meta description quality."""
        if not meta_description:
            return SEOCheckResult(
                name="Meta 描述",
                passed=False,
                score=0,
                message="缺少 Meta 描述",
                recommendation="請新增 150 字以內的 Meta 描述",
            )
        
        length = len(meta_description)
        has_keyword = keyword.lower() in meta_description.lower()
        
        if 120 <= length <= 160 and has_keyword:
            return SEOCheckResult(
                name="Meta 描述",
                passed=True,
                score=100,
                message="Meta 描述長度適中且包含關鍵字",
            )
        elif has_keyword:
            return SEOCheckResult(
                name="Meta 描述",
                passed=True,
                score=70,
                message=f"Meta 描述包含關鍵字，但長度為 {length} 字",
                recommendation="建議控制在 120-160 字之間",
            )
        else:
            return SEOCheckResult(
                name="Meta 描述",
                passed=False,
                score=40,
                message="Meta 描述未包含關鍵字",
                recommendation="建議在 Meta 描述中加入目標關鍵字",
            )
    
    def check_word_count(
        self,
        content: str,
        min_words: int = 1500,
    ) -> SEOCheckResult:
        """Check content word count."""
        # Count CJK + words
        cjk_count = len(re.findall(r'[\u4e00-\u9fff]', content))
        word_count = len(content.split()) + cjk_count
        
        if word_count >= min_words:
            return SEOCheckResult(
                name="內容長度",
                passed=True,
                score=100,
                message=f"內容共 {word_count} 字，符合 SEO 建議長度",
            )
        elif word_count >= min_words * 0.7:
            return SEOCheckResult(
                name="內容長度",
                passed=True,
                score=70,
                message=f"內容共 {word_count} 字",
                recommendation=f"建議增加到 {min_words} 字以上以提升排名",
            )
        else:
            return SEOCheckResult(
                name="內容長度",
                passed=False,
                score=30,
                message=f"內容僅 {word_count} 字，可能過短",
                recommendation=f"建議增加到至少 {min_words} 字",
            )
    
    def check_heading_structure(
        self,
        content: str,
    ) -> SEOCheckResult:
        """Check heading structure in content."""
        h1_count = len(re.findall(r'^#\s+[^\n]+', content, re.MULTILINE))
        h2_count = len(re.findall(r'^##\s+[^\n]+', content, re.MULTILINE))
        h3_count = len(re.findall(r'^###\s+[^\n]+', content, re.MULTILINE))
        
        issues = []
        score = 100
        
        if h1_count == 0:
            issues.append("缺少 H1 標題")
            score -= 30
        elif h1_count > 1:
            issues.append("H1 標題應只有一個")
            score -= 20
        
        if h2_count < 3:
            issues.append("H2 標題過少")
            score -= 20
        
        if h2_count > 0 and h3_count == 0:
            issues.append("建議增加 H3 子標題")
            score -= 10
        
        if not issues:
            return SEOCheckResult(
                name="標題結構",
                passed=True,
                score=100,
                message=f"標題結構良好 (H1:{h1_count}, H2:{h2_count}, H3:{h3_count})",
            )
        else:
            return SEOCheckResult(
                name="標題結構",
                passed=score >= 70,
                score=max(0, score),
                message="; ".join(issues),
                recommendation="優化標題結構以提升可讀性",
            )
    
    def check_keyword_density(
        self,
        content: str,
        keyword: str,
    ) -> SEOCheckResult:
        """Check keyword density in content."""
        content_lower = content.lower()
        keyword_lower = keyword.lower()
        
        # Count occurrences
        occurrences = content_lower.count(keyword_lower)
        word_count = len(content.split()) + len(re.findall(r'[\u4e00-\u9fff]', content))
        
        if word_count == 0:
            density = 0
        else:
            density = (occurrences * len(keyword.split())) / word_count * 100
        
        if 1.0 <= density <= 2.5:
            return SEOCheckResult(
                name="關鍵字密度",
                passed=True,
                score=100,
                message=f"關鍵字密度 {density:.1f}%，在理想範圍內",
            )
        elif 0.5 <= density < 1.0:
            return SEOCheckResult(
                name="關鍵字密度",
                passed=True,
                score=70,
                message=f"關鍵字密度 {density:.1f}%，稍低",
                recommendation="可適當增加關鍵字使用頻率",
            )
        elif 2.5 < density <= 4.0:
            return SEOCheckResult(
                name="關鍵字密度",
                passed=True,
                score=60,
                message=f"關鍵字密度 {density:.1f}%，偏高",
                recommendation="可能被判定為過度優化，建議減少",
            )
        elif density > 4.0:
            return SEOCheckResult(
                name="關鍵字密度",
                passed=False,
                score=20,
                message=f"關鍵字密度 {density:.1f}%，過高！",
                recommendation="關鍵字堆砌可能導致處罰，請減少使用",
            )
        else:
            return SEOCheckResult(
                name="關鍵字密度",
                passed=False,
                score=30,
                message=f"關鍵字密度 {density:.1f}%，過低",
                recommendation="內容中應自然融入更多目標關鍵字",
            )
    
    def analyze(
        self,
        title: str,
        content: str,
        keyword: str,
        meta_description: str = "",
        min_word_count: int = 1500,
    ) -> SEOReport:
        """
        Perform complete SEO analysis.
        
        Args:
            title: Article title
            content: Article content (markdown)
            keyword: Target keyword
            meta_description: Meta description
            min_word_count: Minimum recommended word count
            
        Returns:
            SEOReport with detailed analysis
        """
        checks = [
            self.check_title_keyword(title, keyword),
            self.check_meta_description(meta_description, keyword),
            self.check_word_count(content, min_word_count),
            self.check_heading_structure(content),
            self.check_keyword_density(content, keyword),
        ]
        
        # Calculate weighted score
        total_weight = sum(self.weights.get(check.name, 10) for check in checks)
        weighted_score = sum(
            check.score * self.weights.get(check.name, 10) / total_weight
            for check in checks
        )
        overall_score = round(weighted_score)
        
        # Generate summary
        passed_count = sum(1 for c in checks if c.passed)
        if overall_score >= 80:
            summary = f"SEO 優化良好！通過 {passed_count}/{len(checks)} 項檢查"
        elif overall_score >= 60:
            summary = f"SEO 尚可，建議改進。通過 {passed_count}/{len(checks)} 項檢查"
        else:
            summary = f"SEO 需要改善。通過 {passed_count}/{len(checks)} 項檢查"
        
        return SEOReport(
            overall_score=overall_score,
            checks=checks,
            summary=summary,
        )


# Singleton instance
seo_checker = SEOScoreChecker()
