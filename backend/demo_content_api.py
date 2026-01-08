"""
Content Generation API Demo

This script demonstrates the content generation API endpoints in action.
It simulates real usage patterns and showcases the functionality.
"""

import asyncio
import httpx
import json
from datetime import datetime

class ContentAPIDemo:
    """Demo client for Content Generation API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = None
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
            
    async def test_outline_generation(self):
        """Test outline generation endpoint."""
        print("📝 Testing Outline Generation Endpoint...")
        
        try:
            # Prepare request data
            outline_request = {
                "keyword": "SEO 優化指南",
                "competitor_data": [
                    {
                        "title": "完整的 SEO 優化教學 2024",
                        "headings": ["SEO 基礎", "關鍵字研究", "內容優化", "技術 SEO"]
                    },
                    {
                        "title": "SEO 排名提升秘訣",
                        "headings": ["搜尋意圖分析", "競爭對手研究", "連結建設"]
                    }
                ],
                "target_length": 3000,
                "language": "zh-tw"
            }
            
            # Make API request
            response = await self.client.post(
                f"{self.base_url}/api/v1/content/outline",
                json=outline_request
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ Outline generation successful")
                print(f"   Title: {result['data']['title']}")
                print(f"   Sections: {len(result['data']['outline'])}")
                
                # Show first few outline items
                for i, section in enumerate(result['data']['outline'][:3]):
                    level = section.get('level', 2)
                    heading = section.get('heading', 'Unknown')
                    print(f"      H{level}: {heading}")
                    
                return result['data']
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return None
            
    async def test_section_generation(self):
        """Test section generation endpoint."""
        print("\n🔧 Testing Section Generation Endpoint...")
        
        try:
            # Prepare request data
            section_request = {
                "heading": "SEO 基礎概念",
                "content_points": [
                    "什麼是搜尋引擎優化",
                    "SEO 的重要性和價值",
                    "白帽 SEO vs 黑帽 SEO",
                    "SEO 的主要組成要素"
                ],
                "keyword": "SEO 優化",
                "target_length": 400,
                "language": "zh-tw"
            }
            
            # Make API request
            response = await self.client.post(
                f"{self.base_url}/api/v1/content/section",
                json=section_request
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ Section generation successful")
                print(f"   Heading: {result['data']['heading']}")
                print(f"   Word Count: {result['data']['word_count']}")
                print(f"   Content Preview: {result['data']['content'][:100]}...")
                
                return result['data']
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return None
            
    async def test_content_optimization(self):
        """Test content optimization endpoint."""
        print("\n🎯 Testing Content Optimization Endpoint...")
        
        try:
            # Prepare request data
            original_content = """SEO 是很重要的網路行銷技術。它可以幫助網站在搜尋引擎中獲得更好的排名。
            
SEO 包含多個方面，比如關鍵字優化、內容品質、網站速度等。這些因素都會影響搜尋引擎的排名。

要做好 SEO，需要持續學習和實踐。因為搜尋引擎的算法經常在變化。"""

            optimize_request = {
                "content": original_content,
                "keyword": "SEO 優化",
                "optimization_type": "seo",
                "language": "zh-tw"
            }
            
            # Make API request
            response = await self.client.post(
                f"{self.base_url}/api/v1/content/optimize",
                json=optimize_request
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ Content optimization successful")
                print(f"   Optimization Type: {result['data']['optimization_type']}")
                print(f"   Original Length: {len(result['data']['original_content'])}")
                print(f"   Optimized Preview: {result['data']['optimized_content'][:150]}...")
                
                return result['data']
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return None
            
    async def test_usage_statistics(self):
        """Test usage statistics endpoint."""
        print("\n📊 Testing Usage Statistics Endpoint...")
        
        try:
            # Make API request
            response = await self.client.get(f"{self.base_url}/api/v1/content/usage")
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ Usage statistics retrieved")
                stats = result['data']
                print(f"   Requests: {stats['requests']}")
                print(f"   Tokens Used: {stats['tokens_used']}")
                print(f"   Estimated Cost: ${stats['cost_estimate']:.6f}")
                print(f"   Model: {stats['model']}")
                print(f"   Configured: {stats['configured']}")
                
                return stats
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return None

async def test_server_health():
    """Test if the server is running."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/health")
            
        if response.status_code == 200:
            print("✅ Server is running and healthy")
            return True
        else:
            print(f"⚠️  Server responded with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Server is not running: {e}")
        print("\n💡 To run the server:")
        print("   cd backend")
        print("   uvicorn app.main:app --reload --port 8000")
        return False

async def main():
    """Run the demo."""
    print("🚀 Content Generation API Demo")
    print(f"📅 Demo run at: {datetime.now().isoformat()}")
    print("-" * 60)
    
    # Check if server is running
    if not await test_server_health():
        print("\n❌ Cannot proceed without running server")
        return False
        
    print("\n🎯 Starting API endpoint tests...")
    
    success_count = 0
    total_tests = 4
    
    try:
        async with ContentAPIDemo() as demo:
            # Test 1: Outline Generation
            result1 = await demo.test_outline_generation()
            if result1:
                success_count += 1
                
            # Test 2: Section Generation  
            result2 = await demo.test_section_generation()
            if result2:
                success_count += 1
                
            # Test 3: Content Optimization
            result3 = await demo.test_content_optimization()
            if result3:
                success_count += 1
                
            # Test 4: Usage Statistics
            result4 = await demo.test_usage_statistics()
            if result4:
                success_count += 1
                
    except Exception as e:
        print(f"❌ Demo failed with exception: {e}")
        
    # Summary
    print("\n" + "=" * 60)
    print("📊 DEMO SUMMARY")
    print("=" * 60)
    
    print(f"✅ Successful API calls: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 All API endpoints working correctly!")
        print("\n📋 Content Generation Features Available:")
        print("   ✅ Article Outline Generation")
        print("   ✅ Section Content Generation")
        print("   ✅ Content SEO Optimization")
        print("   ✅ Usage Statistics Tracking")
        print("\n🔑 Note: Currently running in mock mode (no OpenAI API key)")
        print("   Add OPENAI_API_KEY to environment to enable real generation")
    else:
        print("⚠️  Some endpoints failed. Check server logs for details.")
        
    return success_count == total_tests

if __name__ == "__main__":
    asyncio.run(main())