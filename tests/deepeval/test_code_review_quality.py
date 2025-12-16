
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

def test_code_review_quality_security():
    """Evaluate if code reviewer catches a security flaw."""
    
    # Golden Scenario: Hardcoded secret (same as before)
    diff = """diff --git a/config.py b/config.py
index abc..def 100644
--- a/config.py
+++ b/config.py
@@ -10,4 +10,4 @@
-API_KEY = os.getenv("API_KEY")
+API_KEY = "sk-1234567890abcdef"
"""
    
    try:
        from automation_agent.code_reviewer import CodeReviewer
        from automation_agent.llm_client import LLMClient
        from automation_agent.review_provider import LLMReviewProvider
        from unittest.mock import AsyncMock, MagicMock
        
        # Create properly mocked GitHub client
        mock_github = MagicMock()
        mock_github.get_commit_diff = AsyncMock(return_value=diff)
        mock_github.get_commit_info = AsyncMock(return_value={
            "sha": "abc123",
            "commit": {"message": "Test commit with hardcoded secret"}
        })
        mock_github.post_commit_comment = AsyncMock(return_value=True)

        # Use Gemini provider
        llm_client = LLMClient(provider="gemini", model="gemini-2.5-flash")
        provider = LLMReviewProvider(llm_client)
        reviewer = CodeReviewer(mock_github, provider)
        
        import asyncio
        review_result = asyncio.run(reviewer.review_commit(
            commit_sha="abc123",
            post_as_issue=False,
            pr_number=None,
            run_id="deepeval-security-test"
        ))
        
        # Extract review content from result
        if not review_result.get("success"):
            pytest.fail(f"Review failed: {review_result.get('message')}")
        actual_output = review_result["review"]
        
    except Exception as e:
        pytest.fail(f"Could not run CodeReviewer: {e}")

    test_case = LLMTestCase(
        input=diff,
        actual_output=actual_output,
        expected_output="Security vulnerability detected: Hardcoded API key.",
        context=["The reviewer should identify hardcoded credentials and security risks."]
    )

    # Use Gemini as judge
    gemini_judge = DeepEvalGemini()

    correctness_metric = GEval(
        name="Correctness",
        criteria="Determine if the code review correctly identifies the security flaw (hardcoded secret).",
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        model=gemini_judge
    )

    assert_test(test_case, [correctness_metric])

def test_code_review_quality_logic():
    """Evaluate if code reviewer catches a logic bug."""
    
    diff = """diff --git a/calc.py b/calc.py
index abc..def 100644
--- a/calc.py
+++ b/calc.py
@@ -5,3 +5,6 @@
 def calculate_average(numbers):
-    return sum(numbers) / len(numbers) if numbers else 0
+    total = sum(numbers)
+    count = len(numbers)
+    return total / count
"""

    try:
        from automation_agent.code_reviewer import CodeReviewer
        from automation_agent.llm_client import LLMClient
        from automation_agent.review_provider import LLMReviewProvider
        from unittest.mock import AsyncMock, MagicMock
        
        # Create properly mocked GitHub client
        mock_github = MagicMock()
        mock_github.get_commit_diff = AsyncMock(return_value=diff)
        mock_github.get_commit_info = AsyncMock(return_value={
            "sha": "def456",
            "commit": {"message": "Test commit with logic bug"}
        })
        mock_github.post_commit_comment = AsyncMock(return_value=True)
        
        llm_client = LLMClient(provider="gemini", model="gemini-2.5-flash")
        provider = LLMReviewProvider(llm_client)
        reviewer = CodeReviewer(mock_github, provider)
        
        import asyncio
        review_result = asyncio.run(reviewer.review_commit(
            commit_sha="def456",
            post_as_issue=False,
            pr_number=None,
            run_id="deepeval-logic-test"
        ))
        
        # Extract review content from result
        if not review_result.get("success"):
            pytest.fail(f"Review failed: {review_result.get('message')}")
        actual_output = review_result["review"]
    except Exception as e:
        pytest.fail(f"Could not run CodeReviewer: {e}")

    test_case = LLMTestCase(
        input=diff,
        actual_output=actual_output,
        expected_output="Potential ZeroDivisionError if 'numbers' is empty.",
        context=["The reviewer should identify that removing the check for empty list causes division by zero."]
    )

    gemini_judge = DeepEvalGemini()

    correctness_metric = GEval(
        name="Bug Detection",
        criteria="Determine if the code review detects the potential ZeroDivisionError.",
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        model=gemini_judge
    )

    assert_test(test_case, [correctness_metric])
