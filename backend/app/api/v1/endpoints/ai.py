"""
AI Hub Router - API endpoints for AI service integration.

Provides unified interface for multiple AI providers (Zeabur, Google Gemini, etc.)
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_active_user
from app.services.cache_manager import cache_manager
from app.config import settings as app_settings
from app.services.ai_service import AIService

router = APIRouter()

# Cache key for AI settings
AI_SETTINGS_KEY = "system:ai_settings"


class AISettingsModel(BaseModel):
    """AI settings schema."""
    provider: str = Field(default="zeabur", description="AI provider (zeabur, google_gemini)")
    model: str = Field(default="gemini-2.5-flash", description="AI model to use")
    api_key: Optional[str] = Field(default=None, description="AI API Key")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Temperature for generation")


class AITestRequest(BaseModel):
    """AI connection test request."""
    provider: str = Field(default="zeabur", description="AI provider to test")
    model: str = Field(default="gemini-2.5-flash", description="Model to test")
    api_key: Optional[str] = Field(default=None, description="API Key (optional)")


class AIAnalyzeRequest(BaseModel):
    """AI analysis request."""
    data: Dict[str, Any] = Field(..., description="Data to analyze")
    context: str = Field(..., description="Context description")
    provider: Optional[str] = Field(default=None, description="AI provider")
    model: Optional[str] = Field(default=None, description="AI model")
    report_type: str = Field(default="ad_analysis", description="Report type")


@router.get("/providers")
async def get_providers():
    """
    Get available AI providers.

    Returns list of supported AI providers with their descriptions.
    """
    return {
        "providers": AIService.get_available_providers()
    }


@router.get("/models")
async def get_models(provider: str = "zeabur"):
    """
    Get available models for a provider.

    Args:
        provider: AI provider name (zeabur, google_gemini)
    """
    return {
        "models": AIService.get_available_models(provider)
    }


@router.get("/settings")
async def get_ai_settings(
    current_user = Depends(get_current_active_user)
):
    """
    Get current AI settings.

    Returns cached settings or defaults from environment.
    """
    # Try to get from cache first
    cached = await cache_manager.get(AI_SETTINGS_KEY)

    if cached:
        settings_data = cached
    else:
        # Fall back to environment defaults
        settings_data = {
            "provider": "zeabur",
            "model": "gemini-2.5-flash",
            "api_key": "",  # Don't expose from env
            "temperature": 0.7,
        }

    # Mask the API key
    if settings_data.get("api_key"):
        key = settings_data["api_key"]
        if len(key) > 8:
            settings_data["api_key"] = key[:4] + "*" * (len(key) - 8) + key[-4:]
        else:
            settings_data["api_key"] = "****"

    return settings_data


@router.post("/settings")
async def update_ai_settings(
    new_settings: AISettingsModel,
    current_user = Depends(get_current_active_user)
):
    """
    Update AI settings.

    Saves settings to cache for persistence.
    """
    # Get current settings
    cached = await cache_manager.get(AI_SETTINGS_KEY)
    current = cached or {
        "provider": "zeabur",
        "model": "gemini-2.5-flash",
        "api_key": "",
        "temperature": 0.7,
    }

    # Update with new values
    update_data = new_settings.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            current[key] = value

    # Save to cache (persistent)
    await cache_manager.set(AI_SETTINGS_KEY, current, expire_days=365)

    return {"message": "AI 設定已更新", "success": True}


@router.post("/test-connection")
async def test_ai_connection(
    request: AITestRequest,
    current_user = Depends(get_current_active_user)
):
    """
    Test AI service connection.

    Attempts a simple API call to verify connectivity and API key validity.
    """
    # Get API key from request or settings
    api_key = request.api_key

    if not api_key:
        # Try to get from cache
        cached = await cache_manager.get(AI_SETTINGS_KEY)
        if cached:
            api_key = cached.get("api_key")

    try:
        success = AIService.test_connection(
            api_key=api_key,
            provider=request.provider,
            model=request.model
        )

        if success:
            return {
                "service": f"{request.provider}/{request.model}",
                "success": True,
                "message": "連線成功！"
            }
        else:
            return {
                "service": f"{request.provider}/{request.model}",
                "success": False,
                "message": "連線失敗，請檢查 API Key"
            }

    except Exception as e:
        return {
            "service": f"{request.provider}/{request.model}",
            "success": False,
            "message": f"連線錯誤: {str(e)}"
        }


@router.post("/analyze")
async def analyze_data(
    request: AIAnalyzeRequest,
    current_user = Depends(get_current_active_user)
):
    """
    Analyze data using AI (streaming response).

    Returns Server-Sent Events stream with AI analysis.
    """
    # Get settings from cache
    cached = await cache_manager.get(AI_SETTINGS_KEY)

    provider = request.provider
    model = request.model
    api_key = None

    if cached:
        if not provider:
            provider = cached.get("provider", "zeabur")
        if not model:
            model = cached.get("model", "gemini-2.5-flash")
        api_key = cached.get("api_key")
    else:
        provider = provider or "zeabur"
        model = model or "gemini-2.5-flash"

    async def event_generator():
        """Generate Server-Sent Events."""
        try:
            for chunk in AIService.analyze_data(
                data=request.data,
                context=request.context,
                api_key=api_key,
                provider=provider,
                model=model,
                report_type=request.report_type
            ):
                # SSE format: data: <content>\n\n
                yield f"data: {chunk}\n\n"

            # Send completion signal
            yield "data: [DONE]\n\n"

        except Exception as e:
            error_msg = f"Error during analysis: {str(e)}"
            yield f"data: {error_msg}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
