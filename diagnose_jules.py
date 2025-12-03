#!/usr/bin/env python3
"""Diagnose Jules API 404 error."""
import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

async def test_jules_api():
    """Test Jules API connectivity."""
    api_key = os.getenv("JULES_API_KEY")
    api_url = os.getenv("JULES_API_URL")
    
    print("="*80)
    print("🔍 Jules API Diagnostics")
    print("="*80)
    print(f"\n📋 Configuration:")
    print(f"   API URL: {api_url}")
    print(f"   API Key: {'*' * 20}{api_key[-10:] if api_key else 'NOT SET'}")
    
    if not api_key:
        print("\n❌ ERROR: JULES_API_KEY not set in .env")
        return
    
    if not api_url:
        print("\n❌ ERROR: JULES_API_URL not set in .env")
        return
    
    print(f"\n🌐 Testing API endpoint...")
    
    # Test with minimal payload
    payload = {
        "diff": "test diff",
        "context": "github_pr"
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"   POST {api_url}")
            async with session.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                print(f"\n📊 Response:")
                print(f"   Status: {response.status}")
                print(f"   Headers: {dict(response.headers)}")
                
                text = await response.text()
                print(f"   Body: {text[:500]}")
                
                if response.status == 404:
                    print(f"\n❌ 404 Not Found")
                    print(f"\n💡 Possible causes:")
                    print(f"   1. Jules API URL is incorrect")
                    print(f"   2. Jules API service doesn't exist at this endpoint")
                    print(f"   3. API endpoint requires different path/parameters")
                    print(f"\n🔧 Suggestions:")
                    print(f"   - Verify the correct Jules API URL from documentation")
                    print(f"   - Check if Jules API is a real service or if you should use LLM provider")
                    print(f"   - Set REVIEW_PROVIDER=llm in .env to use Gemini instead")
                elif response.status == 401:
                    print(f"\n❌ 401 Unauthorized - API key may be invalid")
                elif response.status == 200:
                    print(f"\n✅ Success! Jules API is working")
                    try:
                        data = await response.json()
                        print(f"   Response data: {data}")
                    except:
                        pass
                else:
                    print(f"\n⚠️ Unexpected status code: {response.status}")
                    
    except asyncio.TimeoutError:
        print(f"\n❌ Timeout connecting to Jules API")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("💡 Recommendation:")
    print("="*80)
    print("If Jules API doesn't exist or isn't working, update your .env:")
    print("   REVIEW_PROVIDER=llm")
    print("\nThis will use Gemini for code reviews instead of Jules.")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_jules_api())
