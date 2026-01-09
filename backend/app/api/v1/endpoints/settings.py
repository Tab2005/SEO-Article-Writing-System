"""
Settings API Endpoints.

Handles system settings and API key configuration.
"""

from typing import Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_active_user
from app.services.cache_manager import cache_manager
from app.config import settings as app_settings

router = APIRouter()

# Settings cache key
SETTINGS_KEY = "system:settings"


class APISettings(BaseModel):
    """API Settings schema."""
    google_api_key: Optional[str] = Field(default="", description="Google Custom Search API Key")
    google_cx_id: Optional[str] = Field(default="", description="Google Custom Search Engine ID")
    openai_api_key: Optional[str] = Field(default="", description="OpenAI API Key")
    google_client_id: Optional[str] = Field(default="", description="Google OAuth Client ID")
    google_client_secret: Optional[str] = Field(default="", description="Google OAuth Client Secret")


class SettingsResponse(BaseModel):
    """Settings response with masked keys."""
    google_api_key: str = ""
    google_cx_id: str = ""
    openai_api_key: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    has_google_api: bool = False
    has_openai_api: bool = False
    has_google_oauth: bool = False


class TestResult(BaseModel):
    """API test result."""
    service: str
    success: bool
    message: str


def mask_key(key: str) -> str:
    """Mask API key for display."""
    if not key or len(key) < 8:
        return ""
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


@router.get("", response_model=SettingsResponse)
async def get_settings(
    current_user = Depends(get_current_active_user)
):
    """
    Get current API settings (masked).
    """
    # Try to get from cache first
    cached = await cache_manager.get(SETTINGS_KEY)
    
    if cached:
        settings_data = cached
    else:
        # Fall back to environment variables
        settings_data = {
            "google_api_key": app_settings.google_api_key or "",
            "google_cx_id": app_settings.google_cx_id or "",
            "openai_api_key": app_settings.openai_api_key or "",
            "google_client_id": app_settings.google_client_id or "",
            "google_client_secret": app_settings.google_client_secret or "",
        }
    
    return SettingsResponse(
        google_api_key=mask_key(settings_data.get("google_api_key", "")),
        google_cx_id=mask_key(settings_data.get("google_cx_id", "")),
        openai_api_key=mask_key(settings_data.get("openai_api_key", "")),
        google_client_id=mask_key(settings_data.get("google_client_id", "")),
        google_client_secret=mask_key(settings_data.get("google_client_secret", "")),
        has_google_api=bool(settings_data.get("google_api_key")),
        has_openai_api=bool(settings_data.get("openai_api_key")),
        has_google_oauth=bool(settings_data.get("google_client_id")),
    )


@router.put("")
async def update_settings(
    new_settings: APISettings,
    current_user = Depends(get_current_active_user)
):
    """
    Update API settings.
    
    Only updates non-empty fields.
    """
    # Get current settings
    cached = await cache_manager.get(SETTINGS_KEY)
    current = cached or {
        "google_api_key": app_settings.google_api_key or "",
        "google_cx_id": app_settings.google_cx_id or "",
        "openai_api_key": app_settings.openai_api_key or "",
        "google_client_id": app_settings.google_client_id or "",
        "google_client_secret": app_settings.google_client_secret or "",
    }
    
    # Update only non-empty fields
    update_data = new_settings.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value:  # Only update if value is not empty
            current[key] = value
    
    # Save to cache (persistent)
    await cache_manager.set(SETTINGS_KEY, current, expire_days=365)
    
    return {"message": "設定已更新", "success": True}


@router.post("/test/google-search", response_model=TestResult)
async def test_google_search(
    current_user = Depends(get_current_active_user)
):
    """
    Test Google Custom Search API connection.
    """
    import httpx
    
    # Get settings
    cached = await cache_manager.get(SETTINGS_KEY)
    if cached:
        api_key = cached.get("google_api_key", "")
        cx_id = cached.get("google_cx_id", "")
    else:
        api_key = app_settings.google_api_key or ""
        cx_id = app_settings.google_cx_id or ""
    
    if not api_key or not cx_id:
        return TestResult(
            service="Google Search",
            success=False,
            message="API Key 或 CX ID 未設定"
        )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": api_key,
                    "cx": cx_id,
                    "q": "test",
                    "num": 1,
                },
                timeout=10,
            )
            
            if response.status_code == 200:
                return TestResult(
                    service="Google Search",
                    success=True,
                    message="連線成功！"
                )
            else:
                error = response.json().get("error", {}).get("message", "未知錯誤")
                return TestResult(
                    service="Google Search",
                    success=False,
                    message=f"API 錯誤: {error}"
                )
    except Exception as e:
        return TestResult(
            service="Google Search",
            success=False,
            message=f"連線失敗: {str(e)}"
        )


@router.post("/test/openai", response_model=TestResult)
async def test_openai(
    current_user = Depends(get_current_active_user)
):
    """
    Test OpenAI API connection.
    """
    import httpx
    
    # Get settings
    cached = await cache_manager.get(SETTINGS_KEY)
    if cached:
        api_key = cached.get("openai_api_key", "")
    else:
        api_key = app_settings.openai_api_key or ""
    
    if not api_key:
        return TestResult(
            service="OpenAI",
            success=False,
            message="API Key 未設定"
        )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10,
            )
            
            if response.status_code == 200:
                return TestResult(
                    service="OpenAI",
                    success=True,
                    message="連線成功！"
                )
            else:
                return TestResult(
                    service="OpenAI",
                    success=False,
                    message=f"API 錯誤: {response.status_code}"
                )
    except Exception as e:
        return TestResult(
            service="OpenAI",
            success=False,
            message=f"連線失敗: {str(e)}"
        )
