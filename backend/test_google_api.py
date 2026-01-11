"""
Test script for Google Custom Search API.
This script tests the API directly to see what data can be retrieved.
"""

import asyncio
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.services.google_search import google_search_service


async def test_google_search():
    """Test Google Custom Search API."""
    
    print("=" * 60)
    print("Google Custom Search API Test")
    print("=" * 60)
    
    # Check configuration
    print("\n📋 Configuration Check:")
    print(f"   API Key: {'✅ Configured' if settings.google_api_key else '❌ Not set'}")
    print(f"   CX ID:   {'✅ Configured' if settings.google_cx_id else '❌ Not set'}")
    
    if not settings.google_api_key or not settings.google_cx_id:
        print("\n❌ Error: Google API not configured!")
        print("\n請在 backend/.env 檔案中設定以下環境變數:")
        print("   GOOGLE_API_KEY=your-api-key")
        print("   GOOGLE_CX_ID=your-cx-id")
        print("\n取得方式:")
        print("   1. 前往 Google Cloud Console: https://console.cloud.google.com/")
        print("   2. 啟用 Custom Search API")
        print("   3. 建立 API 金鑰")
        print("   4. 前往 Programmable Search Engine: https://programmablesearchengine.google.com/")
        print("   5. 建立搜尋引擎並取得 CX ID")
        return
    
    # Test keyword
    test_keyword = "降噪耳機"  # Test keyword in Chinese
    test_market = "tw"
    
    print(f"\n🔍 Testing search with keyword: '{test_keyword}' (market: {test_market})")
    print("-" * 60)
    
    try:
        response = await google_search_service.search(
            keyword=test_keyword,
            market=test_market,
            num_results=5
        )
        
        print(f"\n✅ API Response Successful!")
        print(f"\n📊 Search Statistics:")
        print(f"   Keyword:       {response.keyword}")
        print(f"   Market:        {response.market}")
        print(f"   Total Results: {response.total_results:,}")
        print(f"   Results Fetched: {len(response.results)}")
        print(f"   Cached:        {response.cached}")
        print(f"   Fetched At:    {response.fetched_at}")
        
        print(f"\n📑 Search Results:")
        print("-" * 60)
        
        for result in response.results:
            print(f"\n🔹 Rank #{result.rank}")
            print(f"   Title:   {result.title}")
            print(f"   URL:     {result.url}")
            print(f"   Snippet: {result.snippet[:150]}..." if len(result.snippet) > 150 else f"   Snippet: {result.snippet}")
        
        # Pretty print full response
        print("\n" + "=" * 60)
        print("📄 Full Response (JSON):")
        print("=" * 60)
        print(json.dumps(response.model_dump(), indent=2, default=str, ensure_ascii=False))
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print(f"\nException Type: {type(e).__name__}")
        
        # Check if it's a configuration issue
        if "not configured" in str(e).lower():
            print("\n請確認 .env 檔案中的 GOOGLE_API_KEY 和 GOOGLE_CX_ID 已正確設定")
        elif "rate limit" in str(e).lower():
            print("\nAPI 請求次數已達上限，請稍後再試")
        else:
            import traceback
            traceback.print_exc()
    
    finally:
        await google_search_service.close()


if __name__ == "__main__":
    asyncio.run(test_google_search())
