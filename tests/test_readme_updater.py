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

def test_clean_readme_output(readme_updater):
    """Test cleaning of LLM output."""
    raw = "```markdown\n# Title\nContent\n```"
    cleaned = readme_updater._clean_readme_output(raw)
    assert cleaned == "# Title\nContent"

    raw_no_block = "# Title\nContent"
    cleaned = readme_updater._clean_readme_output(raw_no_block)
    assert cleaned == "# Title\nContent"

@pytest.mark.asyncio
async def test_update_readme_missing_file(readme_updater, mock_github_client, mock_llm_client):
    """Test when README.md is missing."""
    mock_github_client.get_commit_diff.return_value = "diff"
    mock_github_client.get_commit_info.return_value = {"files": []}
    mock_github_client.get_file_content.return_value = None # Missing file
    mock_llm_client.update_readme.return_value = "New README"
    
    result = await readme_updater.update_readme("sha123")
    
    assert result == "New README"
    # Verify it used default content
    call_args = mock_llm_client.update_readme.call_args
    assert "# Project" in call_args[0][1]

@pytest.mark.asyncio
async def test_update_readme_fetch_error(readme_updater, mock_github_client):
    """Test failure when fetching diff or info."""
    mock_github_client.get_commit_diff.return_value = None
    result = await readme_updater.update_readme("sha123")
    assert result is None

    mock_github_client.get_commit_diff.return_value = "diff"
    mock_github_client.get_commit_info.return_value = None
    result = await readme_updater.update_readme("sha123")
    assert result is None

