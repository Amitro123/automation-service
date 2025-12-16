
import pytest
import os
import sys
from deepeval import assert_test
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import GEval

# Add src to path for local execution
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

from .utils import DeepEvalGemini

NO_API_KEY = "GEMINI_API_KEY" not in os.environ
pytestmark = pytest.mark.skipif(NO_API_KEY, reason="DeepEval requires GEMINI_API_KEY")

def test_readme_update_quality():
    """Evaluate if ReadmeUpdater correctly describes changes."""
    
    # Golden Scenario: Adding a new endpoint (same as before)
    diff = """diff --git a/src/api.py b/src/api.py
index abc..def 100644
--- a/src/api.py
+++ b/src/api.py
@@ -20,0 +21,4 @@
+@app.route('/health', methods=['GET'])
+def health_check():
+    return jsonify({"status": "healthy"}), 200
+"""
    
    current_readme = """# Automation Service
    
    ## Endpoints
    - POST /webhook: Receives events.
    """
    
    try:
        from automation_agent.readme_updater import ReadmeUpdater
        from automation_agent.llm_client import LLMClient
        from automation_agent.review_provider import LLMReviewProvider
        
        class MockGitHub:
            async def get_commit_diff(self, sha): return diff
            async def get_commit_info(self, sha): return {"message": "Update"}
            async def get_file_content(self, path, ref): return current_readme
            
        llm_client = LLMClient(provider="gemini", model="gemini-2.5-flash")
        provider = LLMReviewProvider(llm_client)
        updater = ReadmeUpdater(MockGitHub(), provider)
        
        # We need to use asyncio.run because update_readme is async
        import asyncio
        updated_readme = asyncio.run(updater.update_readme("fake_sha"))

        if isinstance(updated_readme, dict):
             updated_text = updated_readme.get("content", current_readme)
        else:
             updated_text = updated_readme

    except Exception as e:
        pytest.fail(f"Could not run ReadmeUpdater: {e}")

    test_case = LLMTestCase(
        input=f"Change: Added /health endpoint.\nDiff:\n{diff}",
        actual_output=updated_text,
        expected_output="Includes /health endpoint documentation.",
        context=["The README should now list the /health endpoint."]
    )

    gemini_judge = DeepEvalGemini()

    relevancy_metric = GEval(
        name="Documentation Completeness",
        criteria="Check if the new /health endpoint is documented in the README text.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        model=gemini_judge
    )

    assert_test(test_case, [relevancy_metric])
