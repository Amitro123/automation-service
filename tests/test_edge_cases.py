"""Edge case tests for automation agent."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.automation_agent.orchestrator import AutomationOrchestrator
from src.automation_agent.code_reviewer import CodeReviewer
from src.automation_agent.readme_updater import ReadmeUpdater
from src.automation_agent.spec_updater import SpecUpdater
from src.automation_agent.config import Config
from src.automation_agent.review_provider import ReviewProvider

@pytest.fixture
def mock_config():
    config = MagicMock(spec=Config)
    config.POST_REVIEW_AS_ISSUE = False
    config.CREATE_PR = False
    config.AUTO_COMMIT = False
    return config

# Test empty diffs
@pytest.mark.asyncio
async def test_empty_diff(mock_config):
    """Test handling of empty diff."""
    mock_github = MagicMock()
    mock_github.get_commit_diff = AsyncMock(return_value="")  # Empty diff
    mock_github.get_commit_info = AsyncMock(return_value={
        "sha": "abc123",
        "commit": {"message": "empty", "author": {"name": "User"}}
    })
    
    mock_provider = MagicMock(spec=ReviewProvider)
    mock_provider.review_code = AsyncMock(return_value=("No changes to review", {}))
    
    reviewer = CodeReviewer(mock_github, mock_provider)
    result = await reviewer.review_commit("abc123")
    
    # Should handle gracefully
    assert result["success"] is False  # No diff means no review posted

@pytest.mark.asyncio
async def test_huge_diff(mock_config):
    """Test handling of very large diff."""
    mock_github = MagicMock()
    # Simulate huge diff (100k lines)
    mock_github.get_commit_diff = AsyncMock(return_value="+" + ("line\n" * 100000))
    mock_github.get_commit_info = AsyncMock(return_value={
        "sha": "abc123",
        "commit": {"message": "huge", "author": {"name": "User"}}
    })
    mock_github.post_commit_comment = AsyncMock(return_value=True)
    
    mock_provider = MagicMock(spec=ReviewProvider)
    mock_provider.review_code = AsyncMock(return_value=("Review of large diff", {"total_tokens": 1000}))
    
    reviewer = CodeReviewer(mock_github, mock_provider)
    result = await reviewer.review_commit("abc123")
    
    # Should still process (LLM client may truncate internally)
    assert result["success"] is True

@pytest.mark.asyncio
async def test_github_rate_limit(mock_config):
    """Test handling of GitHub API rate limit."""
    mock_github = MagicMock()
    # Simulate rate limit error - GitHubClient returns None on error
    mock_github.get_commit_diff = AsyncMock(return_value=None)
    
    mock_provider = MagicMock(spec=ReviewProvider)
    
    reviewer = CodeReviewer(mock_github, mock_provider)
    result = await reviewer.review_commit("abc123")
    
    # Should return False on error
    assert result["success"] is False

@pytest.mark.asyncio
async def test_llm_api_failure(mock_config):
    """Test handling of LLM API failure."""
    mock_github = MagicMock()
    mock_github.get_commit_diff = AsyncMock(return_value="diff")
    mock_github.get_commit_info = AsyncMock(return_value={
        "sha": "abc123",
        "commit": {"message": "test", "author": {"name": "User"}}
    })
    
    mock_provider = MagicMock(spec=ReviewProvider)
    # Simulate LLM API error
    mock_provider.review_code = AsyncMock(side_effect=Exception("API timeout"))
    
    reviewer = CodeReviewer(mock_github, mock_provider)
    result = await reviewer.review_commit("abc123")
    
    # Should handle exception gracefully
    assert result["success"] is False

@pytest.mark.asyncio
async def test_missing_readme(mock_config):
    """Test README update when README.md doesn't exist."""
    mock_github = MagicMock()
    mock_github.get_commit_diff = AsyncMock(return_value="diff")
    mock_github.get_commit_info = AsyncMock(return_value={
        "sha": "abc123",
        "commit": {"message": "test", "author": {"name": "User"}}
    })
    mock_github.get_file_content = AsyncMock(return_value=None)  # README doesn't exist
    
    mock_provider = MagicMock(spec=ReviewProvider)
    mock_provider.update_readme = AsyncMock(return_value=("# New README\n\nContent", {}))
    
    updater = ReadmeUpdater(mock_github, mock_provider)
    result = await updater.update_readme("abc123")
    
    # Should create new README (LLM returns the new content)
    assert result is not None
    assert "# New README" in result

@pytest.mark.asyncio
async def test_missing_spec(mock_config):
    """Test spec update when spec.md doesn't exist."""
    mock_github = AsyncMock()
    mock_github.get_commit_info = AsyncMock(return_value={
        "sha": "abc123",
        "commit": {"message": "test", "author": {"name": "User"}}
    })
    mock_github.get_commit_diff = AsyncMock(return_value="diff content")
    mock_github.get_file_content = AsyncMock(return_value=None)  # spec.md doesn't exist
    
    mock_provider = AsyncMock(spec=ReviewProvider)
    mock_provider.update_spec = AsyncMock(return_value=("New entry", {}))
    
    updater = SpecUpdater(mock_github, mock_provider)
    result = await updater.update_spec("abc123")
    
    # Should create new spec.md
    assert result is not None
    assert "# Project Specification" in result

@pytest.mark.asyncio
async def test_invalid_payload(mock_config):
    """Test orchestrator with invalid webhook payload."""
    mock_github = MagicMock()
    code_reviewer = MagicMock()
    code_reviewer.review_commit = AsyncMock(return_value={"success": False})
    readme_updater = MagicMock()
    readme_updater.update_readme = AsyncMock(return_value=None)
    spec_updater = MagicMock()
    spec_updater.update_spec = AsyncMock(return_value=None)
    code_review_updater = MagicMock()
    code_review_updater.update_review_log = AsyncMock(return_value=None)
    
    mock_session_memory = MagicMock()

    orch = AutomationOrchestrator(
        mock_github, code_reviewer, readme_updater, spec_updater, code_review_updater, mock_session_memory, mock_config
    )
    
    # Invalid payload (missing required fields)
    result = await orch.run_automation({"invalid": "payload"})
    
    assert result["success"] is False
    assert "error" in result

@pytest.mark.asyncio
async def test_malformed_commit_info(mock_config):
    """Test handling of malformed commit info."""
    mock_github = MagicMock()
    mock_github.get_commit_diff = AsyncMock(return_value="diff")
    mock_github.get_commit_info = AsyncMock(return_value=None)  # Malformed response
    
    mock_provider = MagicMock(spec=ReviewProvider)
    
    reviewer = CodeReviewer(mock_github, mock_provider)
    result = await reviewer.review_commit("abc123")
    
    # Should handle gracefully
    assert result["success"] is False
