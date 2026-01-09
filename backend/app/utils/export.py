"""
Export Utilities.

Handles data export to CSV and JSON formats.
"""

import csv
import json
import io
from datetime import datetime
from typing import List, Dict, Any

from app.schemas.research import AnalysisReport, CompetitorData


class ExportService:
    """Service for exporting data in various formats."""
    
    @staticmethod
    def report_to_json(report: AnalysisReport) -> str:
        """Export analysis report as JSON."""
        return json.dumps(report.model_dump(), ensure_ascii=False, indent=2, default=str)
    
    @staticmethod
    def report_to_csv(report: AnalysisReport) -> str:
        """Export analysis report as CSV."""
        output = io.StringIO()
        
        # Write summary section
        output.write("# 關鍵字分析報告\n")
        output.write(f"關鍵字,{report.keyword}\n")
        output.write(f"市場,{report.market}\n")
        output.write(f"平均字數,{report.avg_word_count}\n")
        output.write(f"最小字數,{report.min_word_count}\n")
        output.write(f"最大字數,{report.max_word_count}\n")
        output.write(f"競爭對手數,{report.competitor_count}\n")
        output.write(f"生成時間,{report.generated_at}\n\n")
        
        # Write competitors section
        output.write("# 競爭對手分析\n")
        writer = csv.writer(output)
        writer.writerow(["排名", "標題", "URL", "字數", "H2數量", "Meta描述"])
        
        for comp in report.competitors:
            writer.writerow([
                comp.rank,
                comp.title,
                comp.url,
                comp.word_count,
                len(comp.headings.h2),
                comp.meta_description or "",
            ])
        
        output.write("\n# 常見 H2 標題\n")
        for i, tag in enumerate(report.common_h2_tags, 1):
            output.write(f"{i},{tag}\n")
        
        return output.getvalue()
    
    @staticmethod
    def competitors_to_csv(competitors: List[CompetitorData]) -> str:
        """Export competitors list as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "排名", "標題", "URL", "字數", 
            "H1", "H2標題", "H3標題",
            "Meta描述", "爬取時間"
        ])
        
        for comp in competitors:
            writer.writerow([
                comp.rank,
                comp.title,
                comp.url,
                comp.word_count,
                "; ".join(comp.headings.h1),
                "; ".join(comp.headings.h2),
                "; ".join(comp.headings.h3[:5]),  # Limit H3
                comp.meta_description or "",
                comp.scraped_at,
            ])
        
        return output.getvalue()
    
    @staticmethod
    def seo_report_to_json(seo_report: dict) -> str:
        """Export SEO report as JSON."""
        return json.dumps(seo_report, ensure_ascii=False, indent=2)
    
    @staticmethod
    def articles_to_json(articles: List[Dict[str, Any]]) -> str:
        """Export articles list as JSON."""
        return json.dumps(articles, ensure_ascii=False, indent=2, default=str)
    
    @staticmethod
    def articles_to_csv(articles: List[Dict[str, Any]]) -> str:
        """Export articles list as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "ID", "標題", "目標關鍵字", "狀態",
            "字數", "版本", "建立時間", "更新時間"
        ])
        
        for article in articles:
            writer.writerow([
                article.get("id", ""),
                article.get("title", ""),
                article.get("target_keyword", ""),
                article.get("status", ""),
                article.get("word_count", 0),
                article.get("version", 1),
                article.get("created_at", ""),
                article.get("updated_at", ""),
            ])
        
        return output.getvalue()


# Singleton instance
export_service = ExportService()
