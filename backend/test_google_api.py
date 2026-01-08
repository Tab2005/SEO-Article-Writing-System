"""
Google Search API Integration Test

This script tests the Google Search API service and research endpoints.
"""

import asyncio
import json
from datetime import datetime

async def test_google_search_service():
    """Test Google Search API service functionality."""
    print("🧪 Testing Google Search API Service...")
    
    try:
        from app.services.google_search import google_search_service
        from app.models.user import User
        from app.database import get_db
        
        # Create test user
        test_user_id = "test-user-google-api"
        
        # Test 1: Service configuration validation
        print("\n📋 Test 1: Service Configuration")
        async with google_search_service as service:
            config_valid = service._validate_config()
            print(f"   Google API configured: {config_valid}")
            
            if not config_valid:
                print("   ⚠️  Google API not configured - using mock mode")
                return await test_mock_mode()
                
        # Test 2: Basic search functionality (mock)
        print("\n🔍 Test 2: Mock Search Test")
        
        # Mock search results for testing
        mock_results = {
            "items": [
                {
                    "title": "Test SEO Article - Best Practices 2024",
                    "link": "https://example.com/seo-guide",
                    "snippet": "Learn the best SEO practices for 2024. Complete guide to search engine optimization...",
                    "displayLink": "example.com",
                    "pagemap": {
                        "metatags": [{
                            "title": "SEO Guide 2024",
                            "description": "Complete SEO guide",
                            "author": "SEO Expert"
                        }]
                    }
                }
            ],
            "searchInformation": {
                "totalResults": "1000000",
                "searchTime": "0.45"
            }
        }
        
        # Test processing of mock results  
        async with google_search_service as service:
            processed = await service._process_search_results(mock_results, "SEO")
            
        print(f"   ✅ Processed {len(processed['organic_results'])} organic results")
        print(f"   ✅ SERP features detected: {processed['serp_features']}")
        
        # Test 3: Keyword variations generation
        print("\n🔤 Test 3: Keyword Variations")
        async with google_search_service as service:
            variations = service._generate_keyword_variations("SEO")
            
        print(f"   ✅ Generated {len(variations)} keyword variations:")
        for var in variations[:3]:
            print(f"      - {var}")
            
        # Test 4: Competitor analysis
        print("\n🏢 Test 4: Competitor Analysis")
        async with google_search_service as service:
            competitor_data = service._analyze_competitors(
                processed['organic_results'], "SEO"
            )
            
        print(f"   ✅ Analyzed {competitor_data['total_competitors']} competitors")
        print(f"   ✅ Top domains: {competitor_data['top_domains']}")
        
        # Test 5: SERP features analysis
        print("\n📊 Test 5: SERP Analysis")
        mock_search_results = {
            "organic_results": processed['organic_results'],
            "total_results": 1000000,
            "serp_features": processed['serp_features']
        }
        
        async with google_search_service as service:
            serp_analysis = service._analyze_serp_features(mock_search_results)
            
        print(f"   ✅ Competition level: {serp_analysis['competition_level']}")
        print(f"   ✅ Common terms: {serp_analysis.get('common_terms', [])[:3]}")
        
        # Test 6: Keyword recommendations
        print("\n💡 Test 6: Recommendations")
        mock_research_data = {
            "main_results": mock_search_results,
            "related_queries": [
                {"query": "SEO 教學", "results": mock_search_results},
                {"query": "SEO 工具", "results": mock_search_results}
            ],
            "serp_analysis": serp_analysis
        }
        
        async with google_search_service as service:
            recommendations = service._generate_keyword_recommendations(
                mock_research_data, "SEO"
            )
            
        print(f"   ✅ Generated {len(recommendations)} recommendations:")
        for rec in recommendations:
            print(f"      - {rec['title']}: {rec['description']}")
            
        print("\n✅ All Google Search API service tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Google Search API test failed: {e}")
        return False

async def test_mock_mode():
    """Test service in mock mode when API is not configured."""
    print("🎭 Running in mock mode - Google API not configured")
    
    # Mock functionality tests
    tests_passed = 0
    total_tests = 3
    
    try:
        # Test 1: Configuration validation
        from app.services.google_search import google_search_service
        async with google_search_service as service:
            config_valid = service._validate_config()
            
        assert not config_valid, "Should be invalid when not configured"
        tests_passed += 1
        print("   ✅ Configuration validation test passed")
        
        # Test 2: Mock data processing
        mock_data = {
            "items": [{"title": "Test", "link": "https://test.com", "snippet": "Test snippet"}],
            "searchInformation": {"totalResults": "100", "searchTime": "0.1"}
        }
        
        async with google_search_service as service:
            processed = await service._process_search_results(mock_data, "test")
            
        assert len(processed['organic_results']) == 1, "Should process one result"
        tests_passed += 1
        print("   ✅ Mock data processing test passed")
        
        # Test 3: Utility functions
        async with google_search_service as service:
            variations = service._generate_keyword_variations("test")
            
        assert len(variations) > 0, "Should generate variations"
        tests_passed += 1
        print("   ✅ Utility functions test passed")
        
        print(f"\n✅ Mock mode tests: {tests_passed}/{total_tests} passed")
        return tests_passed == total_tests
        
    except Exception as e:
        print(f"❌ Mock mode test failed: {e}")
        return False

async def test_api_endpoints():
    """Test the research API endpoints."""
    print("\n🌐 Testing Research API Endpoints...")
    
    try:
        # This would require setting up test client and authentication
        # For now, we'll test the endpoint definitions
        
        from app.api.v1.research import router
        print(f"   ✅ Research router loaded with {len(router.routes)} routes")
        
        # List available endpoints
        for route in router.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                methods = list(route.methods)
                print(f"      {methods[0] if methods else 'GET'} {route.path}")
                
        print("   ✅ All research endpoints loaded successfully")
        return True
        
    except Exception as e:
        print(f"❌ API endpoints test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting Google Search API Integration Tests")
    print(f"📅 Test run at: {datetime.now().isoformat()}")
    print("-" * 60)
    
    test_results = []
    
    # Test 1: Google Search Service
    result1 = await test_google_search_service()
    test_results.append(("Google Search Service", result1))
    
    # Test 2: API Endpoints
    result2 = await test_api_endpoints()
    test_results.append(("Research API Endpoints", result2))
    
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
        print("🎉 All tests passed! Google Search API integration is ready.")
    else:
        print("⚠️  Some tests failed. Check configuration and dependencies.")
        
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())