import pytest
from unittest.mock import AsyncMock, Mock
from src.automation_agent.readme_updater import ReadmeUpdater

@pytest.fixture
def readme_updater(mock_github_client, mock_llm_client):
    return ReadmeUpdater(mock_github_client, mock_llm_client)

@pytest.mark.asyncio
async def test_update_readme_success(readme_updater, mock_github_client, mock_llm_client):
    """Test successful README update."""
    mock_github_client.get_commit_diff.return_value = "diff"
    mock_github_client.get_commit_info.return_value = {"files": []}
    mock_github_client.get_file_content.return_value = "Old README"
    mock_llm_client.update_readme.return_value = "New README"
    
    result = await readme_updater.update_readme("sha123")
    
    assert result == "New README"
    mock_llm_client.update_readme.assert_called_once()

@pytest.mark.asyncio
async def test_update_readme_no_changes(readme_updater, mock_github_client, mock_llm_client):
    """Test when no updates are needed."""
    mock_github_client.get_commit_diff.return_value = "diff"
    mock_github_client.get_commit_info.return_value = {"files": []}
    mock_github_client.get_file_content.return_value = "Old README"
    mock_llm_client.update_readme.return_value = "Old README"
    
    result = await readme_updater.update_readme("sha123")
    
    assert result is None

@pytest.mark.asyncio
async def test_update_readme_failure(readme_updater, mock_github_client, mock_llm_client):
    """Test failure in LLM generation."""
    mock_github_client.get_commit_diff.return_value = "diff"
    mock_github_client.get_commit_info.return_value = {"files": []}
    mock_github_client.get_file_content.return_value = "Old README"
    mock_llm_client.update_readme.side_effect = Exception("Error")
    
    result = await readme_updater.update_readme("sha123")
    
    assert result is None
