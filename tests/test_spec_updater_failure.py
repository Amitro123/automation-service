import pytest
from unittest.mock import MagicMock, AsyncMock
from automation_agent.spec_updater import SpecUpdater
from automation_agent.github_client import GitHubClient
from automation_agent.review_provider import ReviewProvider

@pytest.mark.asyncio
async def test_spec_update_failure_returns_dict():
    """Test that SpecUpdater returns an error dictionary on exception."""
    # Mock dependencies
    mock_github = MagicMock(spec=GitHubClient)
    mock_provider = MagicMock(spec=ReviewProvider)
    
    # Mock Github responses
    mock_github.get_commit_info = AsyncMock(return_value={"id": "abc1234"})
    mock_github.get_commit_diff = AsyncMock(return_value="diff content")
    mock_github.get_file_content = AsyncMock(return_value="# Spec")
    
    # Mock Provider to raise exception
    # Use config that would trigger the exception
    mock_provider.update_spec = AsyncMock(side_effect=Exception("Simulated failure"))
    
    # Initialize component
    updater = SpecUpdater(mock_github, mock_provider)
    
    # Run test
    result = await updater.update_spec("abc1234", "main")
    
    # Verification
    assert result is not None
    assert isinstance(result, dict)
    assert result["success"] is False
    assert result["error_type"] == "spec_update_error"
    assert "Simulated failure" in result["message"]
