"""
SEO Check API Endpoints.

Handles SEO analysis and scoring.
"""

from typing import Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse

from app.services.seo_checker import seo_checker, SEOReport
from app.utils.export import export_service

router = APIRouter()


class SEOCheckRequest(BaseModel):
    """Request schema for SEO check."""
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=100)
    keyword: str = Field(..., min_length=1)
    meta_description: str = ""
    min_word_count: int = Field(default=1500, ge=500)


class SEOCheckResponse(BaseModel):
    """Response schema for SEO check."""
    overall_score: int
    summary: str
    checks: list


@router.post("/analyze", response_model=SEOCheckResponse)
async def analyze_seo(request: SEOCheckRequest):
    """
    Analyze content for SEO score.
    
    Returns detailed score breakdown and recommendations.
    """
    report = seo_checker.analyze(
        title=request.title,
        content=request.content,
        keyword=request.keyword,
        meta_description=request.meta_description,
        min_word_count=request.min_word_count,
    )
    
    return SEOCheckResponse(
        overall_score=report.overall_score,
        summary=report.summary,
        checks=[
            {
                "name": check.name,
                "passed": check.passed,
                "score": check.score,
                "message": check.message,
                "recommendation": check.recommendation,
            }
            for check in report.checks
        ],
    )


@router.post("/export/json")
async def export_seo_json(request: SEOCheckRequest):
    """
    Analyze and export SEO report as JSON.
    """
    report = seo_checker.analyze(
        title=request.title,
        content=request.content,
        keyword=request.keyword,
        meta_description=request.meta_description,
        min_word_count=request.min_word_count,
    )
    
    export_data = {
        "overall_score": report.overall_score,
        "summary": report.summary,
        "checks": [
            {
                "name": c.name,
                "passed": c.passed,
                "score": c.score,
                "message": c.message,
                "recommendation": c.recommendation,
            }
            for c in report.checks
        ],
    }
    
    return Response(
        content=export_service.seo_report_to_json(export_data),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=seo-report.json"},
    )
