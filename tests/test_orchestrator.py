import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from automation_agent.orchestrator import AutomationOrchestrator

@pytest.fixture
def orchestrator(mock_github_client, mock_code_reviewer, mock_readme_updater, mock_spec_updater, mock_code_review_updater, mock_config):
    return AutomationOrchestrator(
        github_client=mock_github_client,
        code_reviewer=mock_code_reviewer,
        readme_updater=mock_readme_updater,
        spec_updater=mock_spec_updater,
        code_review_updater=mock_code_review_updater,
        config=mock_config
    )

@pytest.mark.asyncio
async def test_run_automation_success(orchestrator, mock_code_reviewer, mock_readme_updater, mock_spec_updater, mock_code_review_updater, mock_github_client):
    # Setup mocks
    mock_code_reviewer.review_commit.return_value = {"success": True, "review": "Review Content"}
    mock_readme_updater.update_readme.return_value = "Updated README"
    mock_spec_updater.update_spec.return_value = "Updated Spec"
    mock_code_review_updater.update_review_log.return_value = "Updated Log"
    mock_github_client.create_branch.return_value = True
    mock_github_client.update_file.return_value = True
    mock_github_client.create_pull_request.return_value = 123

    payload = {
        "ref": "refs/heads/main",
        "head_commit": {
            "id": "commit_sha_123",
            "message": "feat: test commit"
        }
    }

    result = await orchestrator.run_automation(payload)

    assert result["success"] is True
    assert result["commit_sha"] == "commit_sha_123"
    assert result["branch"] == "main"
    assert result["tasks"]["code_review"]["status"] == "completed"
    assert result["tasks"]["readme_update"]["status"] == "completed"
    assert result["tasks"]["spec_update"]["status"] == "completed"

@pytest.mark.asyncio
async def test_run_automation_invalid_payload(orchestrator):
    payload = {}
    result = await orchestrator.run_automation(payload)
    assert result["success"] is False
    assert result["error"] == "Invalid payload or no commits"

@pytest.mark.asyncio
async def test_extract_diff_info_valid(orchestrator):
    payload = {
        "ref": "refs/heads/feature/test",
        "head_commit": {
            "id": "abc1234",
            "message": "fix: bug"
        }
    }
    info = orchestrator._extract_diff_info(payload)
    assert info["commit_sha"] == "abc1234"
    assert info["branch"] == "feature/test"
    assert info["message"] == "fix: bug"

@pytest.mark.asyncio
async def test_extract_diff_info_invalid(orchestrator):
    payload = {"ref": "refs/heads/main"}
    info = orchestrator._extract_diff_info(payload)
    assert info is None

@pytest.mark.asyncio
async def test_run_parallel_tasks_success(orchestrator):
    async def task1(): return {"success": True}
    async def task2(): return {"success": True}
    
    results = await orchestrator._run_parallel_tasks([task1(), task2()])
    assert len(results) == 2
    assert results[0]["success"] is True
    assert results[1]["success"] is True

@pytest.mark.asyncio
async def test_run_parallel_tasks_exception(orchestrator):
    async def task1(): return {"success": True}
    async def task2(): raise ValueError("Task failed")
    
    results = await orchestrator._run_parallel_tasks([task1(), task2()])
    assert len(results) == 2
    assert results[0]["success"] is True
    assert isinstance(results[1], ValueError)

@pytest.mark.asyncio
async def test_code_review_failure(orchestrator, mock_code_reviewer):
    mock_code_reviewer.review_commit.return_value = {"success": False, "review": None}
    
    payload = {
        "ref": "refs/heads/main",
        "head_commit": {"id": "123", "message": "msg"}
    }
    
    result = await orchestrator.run_automation(payload)
    assert result["success"] is False
    assert result["tasks"]["code_review"]["status"] == "failed"

@pytest.mark.asyncio
async def test_readme_update_skipped(orchestrator, mock_readme_updater):
    mock_readme_updater.update_readme.return_value = None
    
    # Setup other mocks to succeed so we can isolate readme check
    orchestrator.code_reviewer.review_commit.return_value = {"success": True, "review": "Review"}
    orchestrator.spec_updater.update_spec.return_value = "Spec"
    orchestrator.github.create_branch.return_value = True
    orchestrator.github.update_file.return_value = True
    orchestrator.github.create_pull_request.return_value = 123

    payload = {
        "ref": "refs/heads/main",
        "head_commit": {"id": "123", "message": "msg"}
    }
    
    result = await orchestrator.run_automation(payload)
    assert result["tasks"]["readme_update"]["status"] == "skipped"

@pytest.mark.asyncio
async def test_create_documentation_pr_failure_branch(orchestrator, mock_github_client):
    """Test failure when creating branch."""
    mock_github_client.create_branch.return_value = False
    
    result = await orchestrator._create_documentation_pr(
        branch="main", readme_content="content", commit_sha="123"
    )
    
    assert result["success"] is False
    assert result["error"] == "Failed to create branch"

@pytest.mark.asyncio
async def test_create_documentation_pr_failure_update_readme(orchestrator, mock_github_client):
    """Test failure when updating README."""
    mock_github_client.create_branch.return_value = True
    mock_github_client.update_file.return_value = False
    
    result = await orchestrator._create_documentation_pr(
        branch="main", readme_content="content", commit_sha="123"
    )
    
    assert result["success"] is False
    assert result["error"] == "Failed to update README.md"

@pytest.mark.asyncio
async def test_create_documentation_pr_failure_update_spec(orchestrator, mock_github_client):
    """Test failure when updating spec."""
    mock_github_client.create_branch.return_value = True
    mock_github_client.update_file.return_value = False
    
    result = await orchestrator._create_documentation_pr(
        branch="main", spec_content="content", commit_sha="123"
    )
    
    assert result["success"] is False
    assert result["error"] == "Failed to update spec.md"

@pytest.mark.asyncio
async def test_create_documentation_pr_failure_create_pr(orchestrator, mock_github_client):
    """Test failure when creating PR."""
    mock_github_client.create_branch.return_value = True
    mock_github_client.update_file.return_value = True
    mock_github_client.create_pull_request.return_value = None
    
    result = await orchestrator._create_documentation_pr(
        branch="main", readme_content="content", commit_sha="123"
    )
    
    assert result["success"] is False
    assert result["error"] == "Failed to create PR"

@pytest.mark.asyncio
async def test_create_documentation_pr_exception(orchestrator, mock_github_client):
    """Test exception during PR creation."""
    mock_github_client.create_branch.side_effect = Exception("Error")
    
    result = await orchestrator._create_documentation_pr(
        branch="main", readme_content="content", commit_sha="123"
    )
    
    assert result["success"] is False
    assert "Error" in result["error"]

@pytest.mark.asyncio
async def test_readme_update_exception(orchestrator, mock_readme_updater):
    """Test exception in readme update task."""
    mock_readme_updater.update_readme.side_effect = Exception("Error")
    
    result = await orchestrator._run_readme_update("sha", "branch")
    
    assert result["success"] is False
    assert result["status"] == "error"

@pytest.mark.asyncio
async def test_spec_update_exception(orchestrator, mock_spec_updater):
    """Test exception in spec update task."""
    mock_spec_updater.update_spec.side_effect = Exception("Error")
    
    result = await orchestrator._run_spec_update("sha", "branch")
    
    assert result["success"] is False
    assert result["status"] == "error"

@pytest.mark.asyncio
async def test_spec_update_skipped(orchestrator, mock_spec_updater):
    """Test spec update returning None (skipped - no update needed)."""
    mock_spec_updater.update_spec.return_value = None
    
    result = await orchestrator._run_spec_update("sha", "branch")
    
    assert result["success"] is True
    assert result["status"] == "skipped"
    assert result["reason"] == "No updates needed"

@pytest.mark.asyncio
async def test_readme_update_auto_commit(orchestrator, mock_readme_updater, mock_github_client, mock_config):
    """Test README update with AUTO_COMMIT enabled."""
    # Configure mocks
    mock_config.CREATE_PR = False
    mock_config.AUTO_COMMIT = True
    mock_readme_updater.update_readme.return_value = "Updated README"
    mock_github_client.update_file.return_value = True

    result = await orchestrator._run_readme_update("sha123", "main")

    assert result["success"] is True
    assert result["status"] == "completed"
    assert result["auto_committed"] is True
    mock_github_client.update_file.assert_called_once_with(
        file_path="README.md",
        content="Updated README",
        message="docs: Auto-update README.md from sha123",
        branch="main"
    )

@pytest.mark.asyncio
async def test_spec_update_auto_commit(orchestrator, mock_spec_updater, mock_github_client, mock_config):
    """Test spec update with AUTO_COMMIT enabled."""
    # Configure mocks
    mock_config.CREATE_PR = False
    mock_config.AUTO_COMMIT = True
    mock_spec_updater.update_spec.return_value = "Updated Spec"
    mock_github_client.update_file.return_value = True

    result = await orchestrator._run_spec_update("sha123", "main")

    assert result["success"] is True
    assert result["status"] == "completed"
    assert result["auto_committed"] is True
    mock_github_client.update_file.assert_called_once_with(
        file_path="spec.md",
        content="Updated Spec",
        message="docs: Auto-update spec.md from sha123",
        branch="main"
    )
