import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to sys.path
sys.path.append(os.path.join(os.getcwd(), "src"))

from automation_agent.llm_client import LLMClient

# Load environment variables
load_dotenv()

async def main():
    print("🧪 Testing Gemini Code Review on Sample Data...")
    
    # Check for API Key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not found!")
        return

    try:
        # Initialize Client
        client = LLMClient(provider="gemini")
        print(f"✅ LLMClient initialized with model: {client.model}")
        
        # Sample Diff (representing "real data")
        sample_diff = """
diff --git a/src/utils.py b/src/utils.py
index 83a12f..b2c34d 100644
--- a/src/utils.py
+++ b/src/utils.py
@@ -12,6 +12,11 @@ def calculate_metrics(data):
     return {"mean": sum(data)/len(data)}
 
+def unsafe_exec(code):
+    # TODO: Remove this before production
+    exec(code)
+    return True
+
 def format_date(dt):
     return dt.strftime("%Y-%m-%d")
"""
        print(f"\n📄 Analyzing sample diff ({len(sample_diff)} chars)...")
        
        # Run Analysis
        review = await client.analyze_code(sample_diff)
        
        print("\n" + "="*50)
        print("🤖 GEMINI CODE REVIEW RESULT")
        print("="*50)
        print(review)
        print("="*50)
        
        # Save to file for easy reading
        with open("gemini_review_sample.md", "w", encoding="utf-8") as f:
            f.write(review)
        print("\n✅ Review saved to 'gemini_review_sample.md'")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
