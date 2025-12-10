import pytest
from automation_agent.code_review_updater import CodeReviewUpdater
from automation_agent.github_client import GitHubClient
from automation_agent.llm_client import LLMClient
from unittest.mock import MagicMock

def test_log_file_name():
    """Verify that the log file name is correctly set."""
    mock_github = MagicMock(spec=GitHubClient)
    mock_llm = MagicMock(spec=LLMClient)
    
    updater = CodeReviewUpdater(mock_github, mock_llm)
    
    assert updater.LOG_FILE == "AUTOMATED_REVIEWS.md"

def test_initial_log_header():
    """Verify that the initial log header is correct."""
    mock_github = MagicMock(spec=GitHubClient)
    mock_llm = MagicMock(spec=LLMClient)
    
    updater = CodeReviewUpdater(mock_github, mock_llm)
    initial_log = updater._create_initial_log()
    
    assert "# Automated Code Review Log" in initial_log
