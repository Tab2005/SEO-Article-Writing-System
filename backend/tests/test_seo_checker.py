"""
Tests for SEO Score Checker Service.
"""

import pytest
from app.services.seo_checker import seo_checker


class TestSEOChecker:
    """Test SEO checker functionality."""
    
    def test_title_keyword_present_early(self):
        """Test keyword at start of title."""
        result = seo_checker.check_title_keyword(
            title="義大利麵做法：5個簡單步驟",
            keyword="義大利麵做法"
        )
        assert result.passed is True
        assert result.score == 100
    
    def test_title_keyword_present_late(self):
        """Test keyword at end of title."""
        result = seo_checker.check_title_keyword(
            title="5個簡單步驟學會義大利麵做法",
            keyword="義大利麵做法"
        )
        assert result.passed is True
        assert result.score < 100
    
    def test_title_keyword_missing(self):
        """Test missing keyword in title."""
        result = seo_checker.check_title_keyword(
            title="美味料理教學",
            keyword="義大利麵做法"
        )
        assert result.passed is False
        assert result.score == 0
    
    def test_meta_description_optimal(self):
        """Test optimal meta description."""
        result = seo_checker.check_meta_description(
            meta_description="學習義大利麵做法的完整指南，包含5個簡單步驟，讓你在家也能做出美味的義大利麵。從選材到烹飪技巧，一次學會所有秘訣。" * 1,
            keyword="義大利麵做法"
        )
        assert result.passed is True
    
    def test_meta_description_missing(self):
        """Test missing meta description."""
        result = seo_checker.check_meta_description(
            meta_description="",
            keyword="義大利麵做法"
        )
        assert result.passed is False
        assert result.score == 0
    
    def test_word_count_sufficient(self):
        """Test sufficient word count."""
        content = "測試內容 " * 500  # ~500 words
        result = seo_checker.check_word_count(content, min_words=300)
        assert result.passed is True
    
    def test_word_count_insufficient(self):
        """Test insufficient word count."""
        content = "短內容"
        result = seo_checker.check_word_count(content, min_words=1500)
        assert result.passed is False
    
    def test_heading_structure_good(self):
        """Test good heading structure."""
        content = """# 主標題

## 第一節
內容

## 第二節
內容

### 子節
更多內容

## 第三節
內容
"""
        result = seo_checker.check_heading_structure(content)
        assert result.passed is True
        assert result.score >= 80
    
    def test_heading_structure_no_h1(self):
        """Test missing H1."""
        content = """## 第一節
內容

## 第二節
內容
"""
        result = seo_checker.check_heading_structure(content)
        assert result.score < 100
    
    def test_keyword_density_optimal(self):
        """Test optimal keyword density."""
        # ~1.5% density
        content = "義大利麵做法 " + "其他內容 " * 50 + " 義大利麵做法"
        result = seo_checker.check_keyword_density(content, "義大利麵做法")
        # Should be in acceptable range
        assert result.score > 0
    
    def test_full_analysis(self):
        """Test complete SEO analysis."""
        report = seo_checker.analyze(
            title="義大利麵做法：5個簡單步驟在家製作",
            content="""# 義大利麵做法完整指南

## 準備材料
首先我們需要準備義大利麵、番茄醬...

## 烹飪步驟
按照以下義大利麵做法步驟...

### 第一步：煮水
將水煮沸...

### 第二步：下麵
將義大利麵放入...

## 小技巧
掌握這些義大利麵做法技巧...

## 總結
以上就是義大利麵做法的完整說明。
""" * 10,
            keyword="義大利麵做法",
            meta_description="完整的義大利麵做法教學，5個簡單步驟讓你在家輕鬆製作美味義大利麵。",
        )
        
        assert report.overall_score > 0
        assert len(report.checks) >= 4
        assert report.summary
