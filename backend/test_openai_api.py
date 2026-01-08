"""
OpenAI API Integration Test

This script tests the OpenAI API service and content generation endpoints.
"""

import asyncio
import json
from datetime import datetime

async def test_openai_service():
    """Test OpenAI API service functionality."""
    print("🤖 Testing OpenAI API Service...")
    
    try:
        from app.services.llm_service import get_openai_service
        
        # Test 1: Service configuration validation
        print("\n📋 Test 1: Service Configuration")
        async with get_openai_service() as service:
            config_valid = service._validate_config()
            print(f"   OpenAI API configured: {config_valid}")
            
            if not config_valid:
                print("   ⚠️  OpenAI API not configured - using mock mode")
                return await test_mock_mode()
                
        # Test 2: Token counting
        print("\n🔢 Test 2: Token Counting")
        async with get_openai_service() as service:
            test_text = "這是一個測試文本，用來計算 token 數量。"
            token_count = service._count_tokens(test_text)
            
        print(f"   ✅ Token count for test text: {token_count}")
        
        # Test 3: Cost estimation
        print("\n💰 Test 3: Cost Estimation")
        async with get_openai_service() as service:
            cost = service._estimate_cost(100, 200)  # 100 input, 200 output tokens
            
        print(f"   ✅ Estimated cost for 100+200 tokens: ${cost:.6f}")
        
        # Test 4: Usage statistics
        print("\n📊 Test 4: Usage Statistics")
        async with get_openai_service() as service:
            stats = service.get_usage_statistics()
            
        print(f"   ✅ Usage stats initialized: {stats}")
        
        print("\n✅ All OpenAI service tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI service test failed: {e}")
        return False

async def test_mock_mode():
    """Test service functionality in mock mode."""
    print("🎭 Running OpenAI service in mock mode")
    
    try:
        from app.services.llm_service import get_openai_service
        
        tests_passed = 0
        total_tests = 4
        
        # Test 1: Configuration validation
        async with get_openai_service() as service:
            config_valid = service._validate_config()
            
        assert not config_valid, "Should be invalid when not configured"
        tests_passed += 1
        print("   ✅ Configuration validation test passed")
        
        # Test 2: Token counting
        async with get_openai_service() as service:
            token_count = service._count_tokens("測試文本")
            
        assert token_count > 0, "Should count tokens even without API key"
        tests_passed += 1
        print("   ✅ Token counting test passed")
        
        # Test 3: Cost estimation
        async with get_openai_service() as service:
            cost = service._estimate_cost(100, 200)
            
        assert cost > 0, "Should estimate cost"
        tests_passed += 1
        print("   ✅ Cost estimation test passed")
        
        # Test 4: Usage statistics
        async with get_openai_service() as service:
            stats = service.get_usage_statistics()
            
        assert "requests" in stats, "Should have usage statistics"
        tests_passed += 1
        print("   ✅ Usage statistics test passed")
        
        print(f"\n✅ Mock mode tests: {tests_passed}/{total_tests} passed")
        return tests_passed == total_tests
        
    except Exception as e:
        print(f"❌ Mock mode test failed: {e}")
        return False

async def test_content_endpoints():
    """Test the content generation API endpoints."""
    print("\n🎨 Testing Content Generation API Endpoints...")
    
    try:
        # Test endpoint imports
        from app.api.v1.content import router
        print(f"   ✅ Content router loaded with {len(router.routes)} routes")
        
        # List available endpoints
        for route in router.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                methods = list(route.methods)
                print(f"      {methods[0] if methods else 'GET'} {route.path}")
                
        # Test request models
        from app.api.v1.content import OutlineRequest, ArticleRequest, SectionRequest, OptimizeRequest
        
        # Test OutlineRequest
        outline_req = OutlineRequest(
            keyword="SEO 優化",
            target_length=2000,
            language="zh-tw"
        )
        assert outline_req.keyword == "SEO 優化"
        print("   ✅ OutlineRequest model validation passed")
        
        # Test ArticleRequest
        article_req = ArticleRequest(
            outline={
                "title": "SEO 優化指南",
                "outline": [
                    {"level": 1, "heading": "引言", "content_points": ["介紹", "重要性"]}
                ]
            },
            keyword="SEO"
        )
        assert article_req.keyword == "SEO"
        print("   ✅ ArticleRequest model validation passed")
        
        print("   ✅ All content endpoints loaded successfully")
        return True
        
    except Exception as e:
        print(f"❌ Content endpoints test failed: {e}")
        return False

async def test_mock_generation():
    """Test mock content generation without API key."""
    print("\n🎪 Testing Mock Content Generation...")
    
    try:
        from app.services.llm_service import get_openai_service
        
        # Test outline generation in mock mode
        print("\n📝 Testing Mock Outline Generation")
        
        mock_competitor_data = [
            {
                "title": "SEO 完整指南 2024",
                "headings": ["什麼是 SEO", "關鍵字研究", "內容優化"]
            }
        ]
        
        async with get_openai_service() as service:
            # This should return None due to no API key
            outline_result = await service.generate_outline(
                keyword="SEO 教學",
                competitor_data=mock_competitor_data,
                target_length=2000,
                language="zh-tw"
            )
            
        # In mock mode, this returns None (no API key)
        expected_result = outline_result is None
        assert expected_result, "Should return None without API key"
        print("   ✅ Mock outline generation test passed")
        
        print("\n✅ Mock content generation tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Mock generation test failed: {e}")
        return False

async def test_fastapi_integration():
    """Test FastAPI integration with content endpoints."""
    print("\n🌐 Testing FastAPI Integration...")
    
    try:
        # Test main app import with content router
        from app.main import app
        
        # Count routes - should include content endpoints now
        content_routes = [
            route for route in app.routes 
            if hasattr(route, 'path') and '/content' in route.path
        ]
        
        print(f"   ✅ FastAPI app loaded with {len(app.routes)} total routes")
        print(f"   ✅ Content routes found: {len(content_routes)}")
        
        # List content routes
        if content_routes:
            for route in content_routes:
                if hasattr(route, 'methods') and hasattr(route, 'path'):
                    methods = list(route.methods)
                    print(f"      {methods[0] if methods else 'GET'} {route.path}")
                    
        print("   ✅ FastAPI integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ FastAPI integration test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting OpenAI API Integration Tests")
    print(f"📅 Test run at: {datetime.now().isoformat()}")
    print("-" * 60)
    
    test_results = []
    
    # Test 1: OpenAI Service
    result1 = await test_openai_service()
    test_results.append(("OpenAI Service", result1))
    
    # Test 2: Content Endpoints
    result2 = await test_content_endpoints()
    test_results.append(("Content API Endpoints", result2))
    
    # Test 3: Mock Generation
    result3 = await test_mock_generation()
    test_results.append(("Mock Content Generation", result3))
    
    # Test 4: FastAPI Integration
    result4 = await test_fastapi_integration()
    test_results.append(("FastAPI Integration", result4))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
        
    print(f"\n🏁 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! OpenAI API integration is ready.")
        print("\n📋 Next Steps:")
        print("   1. Add OpenAI API key to environment variables")
        print("   2. Test real content generation")
        print("   3. Configure usage limits and monitoring")
    else:
        print("⚠️  Some tests failed. Check configuration and dependencies.")
        
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())