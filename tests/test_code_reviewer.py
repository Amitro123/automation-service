import pytest
from unittest.mock import AsyncMock, Mock, patch
from src.automation_agent.code_reviewer import CodeReviewer

@pytest.fixture
def code_reviewer(mock_github_client, mock_llm_client):
    return CodeReviewer(mock_github_client, mock_llm_client)

@pytest.mark.asyncio
async def test_review_commit_success(code_reviewer, mock_github_client, mock_llm_client):
    """Test successful code review."""
    # Setup mocks
    mock_github_client.get_commit_diff.return_value = "diff content"
    mock_github_client.get_commit_info.return_value = {
        "commit": {
            "message": "test commit",
            "author": {"name": "Test User"}
        }
    }
    mock_llm_client.analyze_code.return_value = "Code review analysis"
    mock_github_client.post_commit_comment.return_value = True

    # Run review
    result = await code_reviewer.review_commit("sha123")

    # Verify
    assert result["success"] is True
    assert "Code review analysis" in result["review"]
    mock_github_client.get_commit_diff.assert_called_once_with("sha123")
    mock_llm_client.analyze_code.assert_called_once_with("diff content")
    mock_github_client.post_commit_comment.assert_called_once()

@pytest.mark.asyncio
async def test_review_commit_no_diff(code_reviewer, mock_github_client):
    """Test review when diff fetch fails."""
    mock_github_client.get_commit_diff.return_value = None
    
    result = await code_reviewer.review_commit("sha123")
    
    assert result["success"] is False

@pytest.mark.asyncio
async def test_review_commit_llm_failure(code_reviewer, mock_github_client, mock_llm_client):
    """Test review when LLM analysis fails."""
    mock_github_client.get_commit_diff.return_value = "diff content"
    mock_github_client.get_commit_info.return_value = {"commit": {}}
    mock_llm_client.analyze_code.side_effect = Exception("LLM Error")
    
    result = await code_reviewer.review_commit("sha123")
    
    assert result["success"] is False

@pytest.mark.asyncio
async def test_review_commit_post_as_issue(code_reviewer, mock_github_client, mock_llm_client):
    """Test posting review as an issue."""
    mock_github_client.get_commit_diff.return_value = "diff content"
    mock_github_client.get_commit_info.return_value = {"commit": {}}
    mock_llm_client.analyze_code.return_value = "Analysis"
    mock_github_client.create_issue.return_value = 123
    
    result = await code_reviewer.review_commit("sha123", post_as_issue=True)
    
    assert result["success"] is True
    mock_github_client.create_issue.assert_called_once()
