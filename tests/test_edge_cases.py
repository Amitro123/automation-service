"""Edge case tests for automation agent."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.automation_agent.orchestrator import AutomationOrchestrator
from src.automation_agent.code_reviewer import CodeReviewer
from src.automation_agent.readme_updater import ReadmeUpdater
from src.automation_agent.spec_updater import SpecUpdater
from src.automation_agent.config import Config

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
    mock_github.get_commit_diff.return_value = ""  # Empty diff
    mock_github.get_commit_info.return_value = {
        "sha": "abc123",
        "commit": {"message": "empty", "author": {"name": "User"}}
    }
    
    mock_llm = MagicMock()
    mock_llm.analyze_code = AsyncMock(return_value="No changes to review")
    
    reviewer = CodeReviewer(mock_github, mock_llm)
    result = await reviewer.review_commit("abc123")
    
    # Should handle gracefully
    assert result is False  # No diff means no review posted

@pytest.mark.asyncio
async def test_huge_diff(mock_config):
    """Test handling of very large diff."""
    mock_github = MagicMock()
    # Simulate huge diff (100k lines)
    mock_github.get_commit_diff.return_value = "+" + ("line\n" * 100000)
    mock_github.get_commit_info.return_value = {
        "sha": "abc123",
        "commit": {"message": "huge", "author": {"name": "User"}}
    }
    mock_github.post_commit_comment.return_value = True
    
    mock_llm = MagicMock()
    mock_llm.analyze_code = AsyncMock(return_value="Review of large diff")
    
    reviewer = CodeReviewer(mock_github, mock_llm)
    result = await reviewer.review_commit("abc123")
    
    # Should still process (LLM client may truncate internally)
    assert result is True

@pytest.mark.asyncio
async def test_github_rate_limit(mock_config):
    """Test handling of GitHub API rate limit."""
    mock_github = MagicMock()
    # Simulate rate limit error - use generic Exception since HTTPError needs response object
    mock_github.get_commit_diff.side_effect = Exception("403 rate limit exceeded")
    
    mock_llm = MagicMock()
    
    reviewer = CodeReviewer(mock_github, mock_llm)
    result = await reviewer.review_commit("abc123")
    
    # Should return False on error
    assert result is False

@pytest.mark.asyncio
async def test_llm_api_failure(mock_config):
    """Test handling of LLM API failure."""
    mock_github = MagicMock()
    mock_github.get_commit_diff.return_value = "diff"
    mock_github.get_commit_info.return_value = {
        "sha": "abc123",
        "commit": {"message": "test", "author": {"name": "User"}}
    }
    
    mock_llm = MagicMock()
    # Simulate LLM API error
    mock_llm.analyze_code = AsyncMock(side_effect=Exception("API timeout"))
    
    reviewer = CodeReviewer(mock_github, mock_llm)
    result = await reviewer.review_commit("abc123")
    
    # Should handle exception gracefully
    assert result is False

@pytest.mark.asyncio
async def test_missing_readme(mock_config):
    """Test README update when README.md doesn't exist."""
    mock_github = MagicMock()
    mock_github.get_commit_diff.return_value = "diff"
    mock_github.get_commit_info.return_value = {
        "sha": "abc123",
        "commit": {"message": "test", "author": {"name": "User"}}
    }
    mock_github.get_file_content.return_value = None  # README doesn't exist
    
    mock_llm = MagicMock()
    mock_llm.update_readme = AsyncMock(return_value="# New README\n\nContent")
    
    updater = ReadmeUpdater(mock_github, mock_llm)
    result = await updater.update_readme("abc123")
    
    # Should create new README (LLM returns the new content)
    assert result is not None
    assert "# New README" in result

@pytest.mark.asyncio
async def test_missing_spec(mock_config):
    """Test spec update when spec.md doesn't exist."""
    mock_github = MagicMock()
    mock_github.get_commit_info.return_value = {
        "sha": "abc123",
        "commit": {"message": "test", "author": {"name": "User"}}
    }
    mock_github.get_file_content.return_value = None  # spec.md doesn't exist
    
    mock_llm = MagicMock()
    mock_llm.update_spec = AsyncMock(return_value="New entry")
    
    updater = SpecUpdater(mock_github, mock_llm)
    result = await updater.update_spec("abc123")
    
    # Should create new spec.md
    assert result is not None
    assert "# Project Specification" in result

@pytest.mark.asyncio
async def test_invalid_payload(mock_config):
    """Test orchestrator with invalid webhook payload."""
    mock_github = MagicMock()
    code_reviewer = MagicMock()
    readme_updater = MagicMock()
    spec_updater = MagicMock()
    
    orch = AutomationOrchestrator(
        mock_github, code_reviewer, readme_updater, spec_updater, mock_config
    )
    
    # Invalid payload (missing required fields)
    result = await orch.run_automation({"invalid": "payload"})
    
    assert result["success"] is False
    assert "error" in result

@pytest.mark.asyncio
async def test_malformed_commit_info(mock_config):
    """Test handling of malformed commit info."""
    mock_github = MagicMock()
    mock_github.get_commit_diff.return_value = "diff"
    mock_github.get_commit_info.return_value = None  # Malformed response
    
    mock_llm = MagicMock()
    
    reviewer = CodeReviewer(mock_github, mock_llm)
    result = await reviewer.review_commit("abc123")
    
    # Should handle gracefully
    assert result is False
