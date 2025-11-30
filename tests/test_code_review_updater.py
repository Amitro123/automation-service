import pytest
from unittest.mock import AsyncMock, MagicMock
from src.automation_agent.code_review_updater import CodeReviewUpdater

@pytest.fixture
def mock_github_client():
    client = AsyncMock()
    return client

@pytest.fixture
def mock_llm_client():
    client = AsyncMock()
    return client

@pytest.fixture
def updater(mock_github_client, mock_llm_client):
    return CodeReviewUpdater(mock_github_client, mock_llm_client)

@pytest.mark.asyncio
async def test_update_review_log_success(updater, mock_github_client, mock_llm_client):
    # Setup
    mock_github_client.get_file_content.return_value = "# Old Log"
    mock_llm_client.summarize_review.return_value = "### New Entry"
    
    # Execute
    result = await updater.update_review_log("sha123", "Review Content", "main")
    
    # Verify
    assert result == "# Old Log\n\n### New Entry\n"
    mock_github_client.get_file_content.assert_called_once_with("code_review.md", ref="main")
    mock_llm_client.summarize_review.assert_called_once()

@pytest.mark.asyncio
async def test_update_review_log_new_file(updater, mock_github_client, mock_llm_client):
    # Setup
    mock_github_client.get_file_content.return_value = None
    mock_llm_client.summarize_review.return_value = "### New Entry"
    
    # Execute
    result = await updater.update_review_log("sha123", "Review Content", "main")
    
    # Verify
    assert "Review History" in result
    assert "### New Entry" in result
    mock_github_client.get_file_content.assert_called_once()

@pytest.mark.asyncio
async def test_update_review_log_llm_failure(updater, mock_github_client, mock_llm_client):
    # Setup
    mock_github_client.get_file_content.return_value = "# Old Log"
    mock_llm_client.summarize_review.side_effect = Exception("LLM Error")
    
    # Execute
    result = await updater.update_review_log("sha123", "Review Content", "main")
    
    # Verify
    assert result is None

@pytest.mark.asyncio
async def test_update_review_log_sanitization(updater, mock_github_client, mock_llm_client):
    # Setup
    mock_github_client.get_file_content.return_value = "# Old Log"
    # LLM returns content wrapped in markdown code block with embedded code block
    mock_llm_client.summarize_review.return_value = "```markdown\n### New Entry\nHere is code:\n```python\ndef foo(): pass\n```\n```"
    
    # Execute
    result = await updater.update_review_log("sha123", "Review Content", "main")
    
    # Verify
    expected_entry = "### New Entry\nHere is code:\n```python\ndef foo(): pass\n```"
    assert result == f"# Old Log\n\n{expected_entry}\n"
    mock_llm_client.summarize_review.assert_called_once()
