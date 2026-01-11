"""Runtime settings resolver.

目的：把「/api/v1/settings 寫入 Redis 的設定」變成後端實際執行時的設定來源（優先），
並在 Redis 不可用或未設定時 fallback 到環境變數（app.config.settings）。

目前主要提供：
- Google Custom Search：api_key / cx_id
- AI：provider / model / api_key

"""

from __future__ import annotations

from typing import Any, Optional, Tuple

from app.config import settings
from app.services.cache_manager import cache_manager

SYSTEM_SETTINGS_KEY = "system:settings"


async def get_system_settings() -> dict[str, Any]:
    cached = await cache_manager.get(SYSTEM_SETTINGS_KEY)
    return cached if isinstance(cached, dict) else {}


async def get_google_search_config() -> Tuple[Optional[str], Optional[str]]:
    data = await get_system_settings()
    api_key = (data.get("google_api_key") or settings.google_api_key) or None
    cx_id = (data.get("google_cx_id") or settings.google_cx_id) or None
    return api_key, cx_id


async def get_ai_config() -> tuple[str, str, Optional[str]]:
    data = await get_system_settings()
    provider = data.get("ai_provider") or getattr(settings, "ai_provider", "zeabur")
    model = data.get("ai_model") or getattr(settings, "ai_model", "gemini-2.5-flash")
    api_key = (data.get("ai_api_key") or getattr(settings, "ai_api_key", None)) or None
    return provider, model, api_key
