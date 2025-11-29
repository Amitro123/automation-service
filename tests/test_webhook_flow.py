"""Integration test for webhook flow - tests orchestrator coordination."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.automation_agent.orchestrator import AutomationOrchestrator
from src.automation_agent.config import Config

@pytest.fixture
def mock_config():
    config = MagicMock(spec=Config)
    config.POST_REVIEW_AS_ISSUE = False
    config.CREATE_PR = True
    config.AUTO_COMMIT = False
    return config

@pytest.fixture
def mock_github_client():
    mock = MagicMock()
    mock.get_commit_diff.return_value = "diff content"
    mock.get_commit_info.return_value = {
        "sha": "abc123",
        "commit": {"message": "feat: test", "author": {"name": "User"}}
    }
    mock.get_file_content.return_value = "Old content"
    mock.create_branch.return_value = True
    mock.update_file.return_value = True
    mock.create_pull_request.return_value = 100
    mock.post_commit_comment.return_value = True
    return mock

@pytest.fixture
def mock_llm_client():
    mock = MagicMock()
    mock.analyze_code = AsyncMock(return_value="Code review")
    mock.update_readme = AsyncMock(return_value="New README")
    mock.update_spec = AsyncMock(return_value="New spec entry")
    return mock

@pytest.fixture
def orchestrator(mock_config, mock_github_client, mock_llm_client):
    # Create mock components
    code_reviewer = MagicMock()
    code_reviewer.review_commit = AsyncMock(return_value=True)
    
    readme_updater = MagicMock()
    readme_updater.update_readme = AsyncMock(return_value="New README")
    
    spec_updater = MagicMock()
    spec_updater.update_spec = AsyncMock(return_value="New spec")
    
    # Create orchestrator with mocked dependencies
    orch = AutomationOrchestrator(
        github_client=mock_github_client,
        code_reviewer=code_reviewer,
        readme_updater=readme_updater,
        spec_updater=spec_updater,
        config=mock_config
    )
    return orch, code_reviewer, readme_updater, spec_updater, mock_github_client

@pytest.mark.asyncio
async def test_orchestrator_runs_all_tasks(orchestrator):
    orch, code_reviewer, readme_updater, spec_updater, mock_github = orchestrator
    
    payload = {
        "ref": "refs/heads/main",
        "commits": [{"id": "abc123"}],
        "head_commit": {"id": "abc123"}
    }
    
    result = await orch.run_automation(payload)
    
    # Verify all three tasks were called
    code_reviewer.review_commit.assert_called_once_with(commit_sha="abc123", post_as_issue=False)
    readme_updater.update_readme.assert_called_once_with(commit_sha="abc123", branch="main")
    spec_updater.update_spec.assert_called_once_with(commit_sha="abc123", branch="main")
    
    # Verify result structure
    assert result["success"] is True
    assert result["commit_sha"] == "abc123"
    assert result["branch"] == "main"

@pytest.mark.asyncio
async def test_orchestrator_creates_pr_for_docs(orchestrator):
    orch, code_reviewer, readme_updater, spec_updater, mock_github = orchestrator
    
    payload = {
        "ref": "refs/heads/main",
        "commits": [{"id": "abc123"}],
        "head_commit": {"id": "abc123"}
    }
    
    await orch.run_automation(payload)
    
    # Verify PR creation was attempted (since CREATE_PR=True and updates returned content)
    assert mock_github.create_pull_request.call_count >= 1

@pytest.mark.asyncio
async def test_orchestrator_handles_no_commits(orchestrator):
    orch, code_reviewer, readme_updater, spec_updater, mock_github = orchestrator
    
    payload = {
        "ref": "refs/heads/main",
        "commits": [],
        "head_commit": None
    }
    
    await orch.run_automation(payload)
    
    # Should not call any tasks
    code_reviewer.review_commit.assert_not_called()
    readme_updater.update_readme.assert_not_called()
    spec_updater.update_spec.assert_not_called()

@pytest.mark.asyncio
async def test_orchestrator_task_failure_doesnt_block_others(orchestrator):
    orch, code_reviewer, readme_updater, spec_updater, mock_github = orchestrator
    
    # Make code reviewer fail
    code_reviewer.review_commit.side_effect = Exception("Review failed")
    
    payload = {
        "ref": "refs/heads/main",
        "commits": [{"id": "abc123"}],
        "head_commit": {"id": "abc123"}
    }
    
    # Should not raise exception
    await orch.run_automation(payload)
    
    # Other tasks should still be called
    readme_updater.update_readme.assert_called_once()
    spec_updater.update_spec.assert_called_once()
