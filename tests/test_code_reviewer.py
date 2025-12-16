import pytest
from unittest.mock import AsyncMock, Mock, patch
from src.automation_agent.code_reviewer import CodeReviewer
from src.automation_agent.review_provider import ReviewProvider

@pytest.fixture
def mock_provider():
    provider = Mock(spec=ReviewProvider)
    provider.review_code = AsyncMock()
    return provider

@pytest.fixture
def code_reviewer(mock_github_client, mock_provider):
    return CodeReviewer(mock_github_client, mock_provider)

@pytest.mark.asyncio
async def test_review_commit_success(code_reviewer, mock_github_client, mock_provider):
    """Test successful code review."""
    # Setup mocks
    mock_github_client.get_commit_diff.return_value = "diff content"
    mock_github_client.get_commit_info.return_value = {
        "commit": {
            "message": "test commit",
            "author": {"name": "Test User"}
        }
    }
    mock_provider.review_code.return_value = ("Code review analysis", {"provider": "test", "total_tokens": 100})
    mock_github_client.post_commit_comment.return_value = True

    # Run review
    result = await code_reviewer.review_commit("sha123")

    # Verify
    assert result["success"] is True
    assert "Code review analysis" in result["review"]
    assert "usage_metadata" in result
    mock_github_client.get_commit_diff.assert_called_once_with("sha123")
    mock_provider.review_code.assert_called_once_with("diff content", "")  # Now includes past_lessons
    mock_github_client.post_commit_comment.assert_called_once()

@pytest.mark.asyncio
async def test_review_commit_no_diff(code_reviewer, mock_github_client):
    """Test review when diff fetch fails."""
    mock_github_client.get_commit_diff.return_value = None
    
    result = await code_reviewer.review_commit("sha123")
    
    assert result["success"] is False

@pytest.mark.asyncio
async def test_review_commit_provider_failure(code_reviewer, mock_github_client, mock_provider):
    """Test review when provider analysis fails."""
    mock_github_client.get_commit_diff.return_value = "diff content"
    mock_github_client.get_commit_info.return_value = {"commit": {}}
    mock_provider.review_code.side_effect = Exception("Provider Error")
    
    result = await code_reviewer.review_commit("sha123")
    
    assert result["success"] is False

@pytest.mark.asyncio
async def test_review_commit_post_as_issue(code_reviewer, mock_github_client, mock_provider):
    """Test posting review as an issue."""
    mock_github_client.get_commit_diff.return_value = "diff content"
    mock_github_client.get_commit_info.return_value = {"commit": {}}
    mock_provider.review_code.return_value = ("Analysis", {"provider": "test"})
    mock_github_client.create_issue.return_value = 123
    
    result = await code_reviewer.review_commit("sha123", post_as_issue=True)
    
    assert result["success"] is True
    assert "usage_metadata" in result
    mock_github_client.create_issue.assert_called_once()
