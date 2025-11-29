import pytest
from unittest.mock import AsyncMock, Mock
from src.automation_agent.spec_updater import SpecUpdater

@pytest.fixture
def spec_updater(mock_github_client, mock_llm_client):
    return SpecUpdater(mock_github_client, mock_llm_client)

@pytest.mark.asyncio
async def test_update_spec_success(spec_updater, mock_github_client, mock_llm_client):
    """Test successful spec update."""
    mock_github_client.get_commit_info.return_value = {
        "sha": "sha123",
        "commit": {"message": "msg", "author": {"name": "User"}}
    }
    mock_github_client.get_commit_diff.return_value = "diff"
    mock_github_client.get_file_content.return_value = "Old Spec Content"
    mock_github_client.get_recent_commits.return_value = []
    
    # LLM returns ONLY the new entry
    mock_llm_client.update_spec.return_value = "New Entry"
    
    result = await spec_updater.update_spec("sha123")
    
    # Verify result contains old content and new entry
    assert "Old Spec Content" in result
    assert "New Entry" in result
    # Verify old content is NOT duplicated (simple check)
    assert result.count("Old Spec Content") == 1

    mock_llm_client.update_spec.assert_called_once()

@pytest.mark.asyncio
async def test_update_spec_failure(spec_updater, mock_github_client, mock_llm_client):
    """Test failure in spec update."""
    mock_github_client.get_commit_info.return_value = {"sha": "sha123"}
    mock_llm_client.update_spec.side_effect = Exception("Error")
    
    result = await spec_updater.update_spec("sha123")
    
    assert result is None

@pytest.mark.asyncio
async def test_update_spec_no_commit_info(spec_updater, mock_github_client):
    """Test failure when commit info is missing."""
    mock_github_client.get_commit_info.return_value = None
    
    result = await spec_updater.update_spec("sha123")
    
    assert result is None

@pytest.mark.asyncio
async def test_update_spec_create_new(spec_updater, mock_github_client, mock_llm_client):
    """Test creating a new spec.md if it doesn't exist."""
    mock_github_client.get_commit_info.return_value = {
        "sha": "sha123",
        "commit": {"message": "msg", "author": {"name": "User"}}
    }
    mock_github_client.get_file_content.return_value = None  # Spec doesn't exist
    mock_llm_client.update_spec.return_value = "New Entry"
    
    result = await spec_updater.update_spec("sha123")
    
    assert "# Project Specification & Progress" in result
    assert "New Entry" in result

@pytest.mark.asyncio
async def test_update_spec_llm_returns_empty(spec_updater, mock_github_client, mock_llm_client):
    """Test failure when LLM returns empty string."""
    mock_github_client.get_commit_info.return_value = {"sha": "sha123"}
    mock_github_client.get_file_content.return_value = "Old Spec"
    mock_llm_client.update_spec.return_value = ""
    
    result = await spec_updater.update_spec("sha123")
    
    assert result is None
