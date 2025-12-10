import pytest
import os

def pytest_runtest_setup(item):
    """
    Skip DeepEval tests if GEMINI_API_KEY is not set.
    """
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not set, skipping AI evaluation tests")
