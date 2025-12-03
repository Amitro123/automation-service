#!/usr/bin/env python3
"""Test Jules API integration for code reviews."""
import os
import asyncio
from dotenv import load_dotenv
from src.automation_agent.config import Config
from src.automation_agent.review_provider import JulesReviewProvider, LLMReviewProvider
from src.automation_agent.llm_client import LLMClient

load_dotenv()

# Sample diff for testing
SAMPLE_DIFF = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,5 +1,8 @@
 def hello():
-    print("Hello")
+    print("Hello, World!")
+    return True
 
 def goodbye():
     print("Goodbye")
+    # TODO: Add proper cleanup
+    return False
"""

async def test_jules_api():
    """Test Jules API code review functionality."""
    print("="*80)
    print("🧪 Testing Jules API Integration")
    print("="*80)
    
    # Load configuration
    config = Config()
    
    print(f"\n📋 Configuration:")
    print(f"   REVIEW_PROVIDER: {config.REVIEW_PROVIDER}")
    print(f"   JULES_API_URL: {config.JULES_API_URL}")
    print(f"   JULES_API_KEY: {'*' * 20}{config.JULES_API_KEY[-10:] if config.JULES_API_KEY else 'NOT SET'}")
    print(f"   JULES_SOURCE_ID: {config.JULES_SOURCE_ID or 'NOT SET'}")
    print(f"   JULES_PROJECT_ID: {config.JULES_PROJECT_ID or 'NOT SET'}")
    
    # Validate configuration
    errors = config.validate()
    if errors:
        print(f"\n❌ Configuration Errors:")
        for error in errors:
            print(f"   - {error}")
        print(f"\n💡 Fix these errors in your .env file before proceeding.")
        return
    
    print(f"\n✅ Configuration valid!")
    
    # Create providers
    print(f"\n🔧 Creating providers...")
    llm_client = LLMClient(config)
    llm_provider = LLMReviewProvider(llm_client)
    jules_provider = JulesReviewProvider(config, llm_provider)
    
    # Test Jules API
    print(f"\n🚀 Testing Jules API with sample diff...")
    print(f"   Diff size: {len(SAMPLE_DIFF)} chars")
    print(f"   Creating Jules session...")
    
    try:
        result, metadata = await jules_provider.review_code(SAMPLE_DIFF)
        
        print(f"\n📊 Result:")
        print(f"   Type: {type(result).__name__}")
        
        if isinstance(result, dict):
            # Error response
            success = result.get("success", False)
            error_type = result.get("error_type", "unknown")
            message = result.get("message", "No message")
            status_code = result.get("status_code", "N/A")
            
            print(f"   Success: {success}")
            print(f"   Error Type: {error_type}")
            print(f"   Status Code: {status_code}")
            print(f"   Message: {message}")
            
            if error_type == "jules_404":
                print(f"\n❌ Jules API 404 Error")
                print(f"\n💡 Troubleshooting:")
                print(f"   1. Verify JULES_SOURCE_ID is correct")
                print(f"   2. List your sources:")
                print(f"      curl 'https://jules.googleapis.com/v1alpha/sources' \\")
                print(f"        -H 'X-Goog-Api-Key: YOUR_API_KEY'")
                print(f"   3. Make sure the source exists and you have access")
                
            elif error_type == "jules_auth_error":
                print(f"\n❌ Jules API Authentication Error")
                print(f"\n💡 Troubleshooting:")
                print(f"   1. Verify JULES_API_KEY is correct")
                print(f"   2. Get a new API key from: https://developers.google.com/jules/api")
                print(f"   3. Make sure the API key has proper permissions")
                
            else:
                print(f"\n⚠️ Jules API Error: {error_type}")
                
        elif isinstance(result, str):
            # Success response
            print(f"   Success: True")
            print(f"   Review Length: {len(result)} chars")
            print(f"   Metadata: {metadata}")
            print(f"\n✅ Jules API Review:")
            print(f"{'='*80}")
            print(result[:500])  # Show first 500 chars
            if len(result) > 500:
                print(f"\n... ({len(result) - 500} more chars)")
            print(f"{'='*80}")
            
            print(f"\n🎉 SUCCESS! Jules API is working correctly!")
            
        else:
            print(f"   Unexpected result type: {type(result)}")
            
    except Exception as e:
        print(f"\n❌ Exception occurred:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n" + "="*80)
    print(f"💡 Next Steps:")
    print(f"="*80)
    
    if config.REVIEW_PROVIDER == "jules":
        print(f"✅ REVIEW_PROVIDER is set to 'jules'")
        print(f"   Your automation will use Jules for code reviews.")
    else:
        print(f"⚠️  REVIEW_PROVIDER is set to '{config.REVIEW_PROVIDER}'")
        print(f"   To use Jules, update your .env:")
        print(f"   REVIEW_PROVIDER=jules")
    
    print(f"\n📚 Resources:")
    print(f"   - Jules API Docs: https://developers.google.com/jules/api")
    print(f"   - Get API Key: https://developers.google.com/jules/api#authentication")
    print(f"   - List Sources: curl 'https://jules.googleapis.com/v1alpha/sources' -H 'X-Goog-Api-Key: YOUR_KEY'")
    print(f"="*80)

if __name__ == "__main__":
    asyncio.run(test_jules_api())
