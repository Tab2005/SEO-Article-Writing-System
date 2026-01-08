"""
Research API endpoints for SEO keyword research and competitor analysis.

This module provides endpoints for:
- Google Search API integration
- Keyword research and analysis
- SERP (Search Engine Results Pages) analysis
- Competitor research and content analysis
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from datetime import datetime

from app.database import get_db
from app.services.google_search import google_search_service
from app.api.dependencies import get_current_user, rate_limit_check
from app.schemas.user import AuthenticatedUser
from app.models.search_cache import SearchCache
from app.schemas.base import BaseResponse

router = APIRouter()

class SearchRequest(BaseResponse):
    """Search request model."""
    query: str
    language: str = "zh-TW"
    country: str = "TW" 
    num_results: int = 10
    project_id: Optional[str] = None
    use_cache: bool = True

class KeywordResearchRequest(BaseResponse):
    """Keyword research request model."""
    seed_keyword: str
    language: str = "zh-TW"
    country: str = "TW"
    project_id: Optional[str] = None
    include_variations: bool = True

@router.get("/health")
async def research_health():
    """Health check for research services."""
    try:
        # Test Google API configuration
        async with google_search_service as service:
            config_valid = service._validate_config()
            
        return {
            "status": "healthy",
            "google_api_configured": config_valid,
            "services": {
                "google_search": "available" if config_valid else "not_configured",
                "search_cache": "active"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from typing import Dict, Any
from datetime import datetime

# 將在後續任務中實作
# from app.schemas.research import ResearchRequest, ResearchResponse
# from app.services.serp_service import SERPService
# from app.tasks.crawler_tasks import crawl_competitors_task

router = APIRouter()

@router.post("/keyword", response_model=dict)
async def start_keyword_research(
    keyword_data: dict,  # 暫時使用 dict，後續會改為 ResearchRequest
    background_tasks: BackgroundTasks
):
    """
    開始關鍵字研究
    
    處理流程：
    1. 驗證輸入參數
    2. 檢查快取中是否已有結果
    3. 觸發背景任務進行 SERP 抓取和競品分析
    4. 返回任務 ID 供客戶端查詢進度
    
    TODO: 實作關鍵字研究邏輯
    """
    return {
        "message": "Keyword research started - TODO: implement", 
        "task_id": "mock-task-123",
        "keyword": keyword_data.get("keyword", "未指定")
    }

@router.post("/search")
async def perform_search(
    search_request: SearchRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    rate_limit: dict = Depends(rate_limit_check),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform Google Custom Search with caching.
    
    This endpoint allows users to search Google and get structured results
    with automatic caching for efficiency.
    """
    try:
        # Validate request
        if not search_request.query or len(search_request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Search query cannot be empty")
            
        if search_request.num_results > 10:
            search_request.num_results = 10  # Google API limitation
            
        # Perform search
        async with google_search_service as service:
            results = await service.search(
                query=search_request.query,
                language=search_request.language,
                country=search_request.country,
                num_results=search_request.num_results,
                user_id=current_user.id,
                project_id=search_request.project_id,
                use_cache=search_request.use_cache
            )
            
        # Note: AuthenticatedUser is from JWT token, not database model
        # API usage tracking would be handled in database operations
        await db.commit()
            
        return {
            "success": True,
            "message": "Search completed successfully",
            "data": {
                "query": search_request.query,
                "language": search_request.language,
                "country": search_request.country,
                "cached": results.get("cached", False),
                "search_time": results.get("search_time", 0),
                "total_results": results.get("total_results", 0),
                "organic_results": results.get("organic_results", []),
                "serp_features": results.get("serp_features", {}),
                "cache_id": results.get("cache_id")
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/keyword-research")
async def keyword_research(
    research_request: KeywordResearchRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    rate_limit: dict = Depends(rate_limit_check),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform comprehensive keyword research and analysis.
    
    This endpoint analyzes a seed keyword and provides:
    - Search volume and competition data
    - Related keyword suggestions  
    - Competitor analysis
    - SERP feature analysis
    - Content recommendations
    """
    try:
        # Validate request
        if not research_request.seed_keyword or len(research_request.seed_keyword.strip()) == 0:
            raise HTTPException(status_code=400, detail="Seed keyword cannot be empty")
            
        # Check API usage limits (would check against database user record)
        # For now, skip API limit checks with AuthenticatedUser
        
        # Perform keyword research
        async with google_search_service as service:
            research_results = await service.keyword_research(
                seed_keyword=research_request.seed_keyword,
                language=research_request.language,
                country=research_request.country,
                user_id=current_user.id,
                project_id=research_request.project_id
            )
            
        # Note: API usage tracking would be handled via database operations
        # with the actual User database model, not the JWT AuthenticatedUser
        
        return {
            "success": True,
            "message": "Keyword research completed successfully",
            "data": {
                "seed_keyword": research_request.seed_keyword,
                "language": research_request.language,
                "country": research_request.country,
                "main_results": research_results.get("main_results", {}),
                "related_queries": research_results.get("related_queries", []),
                "competitor_analysis": research_results.get("competitor_analysis", {}),
                "serp_analysis": research_results.get("serp_analysis", {}),
                "recommendations": research_results.get("recommendations", []),
                "research_timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Keyword research failed: {str(e)}")

@router.get("/search-history")
async def get_search_history(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's search history with optional project filtering."""
    try:
        from sqlalchemy import select, desc
        
        # Build query
        query = select(SearchCache).where(SearchCache.user_id == current_user.id)
        
        if project_id:
            query = query.where(SearchCache.project_id == project_id)
            
        query = query.order_by(desc(SearchCache.created_at)).limit(limit).offset(offset)
        
        # Execute query
        result = await db.execute(query)
        search_history = result.scalars().all()
        
        # Convert to dict format
        history_data = []
        for cache_entry in search_history:
            history_data.append({
                "id": cache_entry.id,
                "query": cache_entry.query,
                "language": cache_entry.language,
                "country": cache_entry.country,
                "total_results": cache_entry.total_results,
                "search_time": cache_entry.search_time,
                "hit_count": cache_entry.hit_count,
                "project_id": cache_entry.project_id,
                "created_at": cache_entry.created_at.isoformat(),
                "last_accessed": cache_entry.last_accessed.isoformat(),
                "analyzed": cache_entry.analyzed
            })
            
        return {
            "success": True,
            "message": f"Retrieved {len(history_data)} search history entries",
            "data": {
                "searches": history_data,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": len(history_data)
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve search history: {str(e)}")

@router.get("/search/{cache_id}")
async def get_cached_search(
    cache_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve a specific cached search result."""
    try:
        from sqlalchemy import select
        
        # Find the cached search
        result = await db.execute(
            select(SearchCache).where(
                SearchCache.id == cache_id,
                SearchCache.user_id == current_user.id
            )
        )
        cache_entry = result.scalar_one_or_none()
        
        if not cache_entry:
            raise HTTPException(status_code=404, detail="Cached search not found")
            
        # Update access count
        cache_entry.increment_hit_count()
        await db.commit()
        
        return {
            "success": True,
            "message": "Cached search retrieved successfully",
            "data": cache_entry.to_dict(include_results=True)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cached search: {str(e)}")

@router.get("/{task_id}/competitors", response_model=dict)
async def get_competitor_details(task_id: str):
    """
    獲取競品詳細資料
    
    返回競品網站的詳細分析：
    - 標題結構 (H1, H2, H3)
    - 字數統計
    - 關鍵字密度
    - Meta 標籤資訊
    
    TODO: 實作競品詳細資料查詢
    """
    return {
        "message": "Get competitor details endpoint - TODO: implement",
        "task_id": task_id
    }

@router.post("/{task_id}/export", response_model=dict)
async def export_research_result(task_id: str, export_format: str = "json"):
    """
    匯出研究結果
    
    支援格式：
    - JSON: 完整結構化資料
    - CSV: 表格格式，適合 Excel 開啟
    - PDF: 報告格式
    
    TODO: 實作資料匯出功能
    """
    return {
        "message": "Export research result endpoint - TODO: implement",
        "task_id": task_id,
        "format": export_format
    }

@router.delete("/{task_id}", response_model=dict)
async def delete_research_result(task_id: str):
    """
    刪除研究結果
    
    清理資料：
    - 刪除資料庫記錄
    - 清除 Redis 快取
    - 移除相關檔案
    
    TODO: 實作結果刪除功能
    """
    return {
        "message": "Delete research result endpoint - TODO: implement",
        "task_id": task_id
    }