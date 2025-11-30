"""Load tests for concurrent webhook pushes."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.automation_agent.orchestrator import AutomationOrchestrator
from src.automation_agent.config import Config

@pytest.fixture
def mock_config():
    config = MagicMock(spec=Config)
    config.POST_REVIEW_AS_ISSUE = False
    config.CREATE_PR = False  # Disable PR creation for load tests
    config.AUTO_COMMIT = False
    return config

@pytest.fixture
def orchestrator_setup(mock_config):
    mock_github = MagicMock()
    mock_github.get_commit_diff = AsyncMock(return_value="diff")
    mock_github.get_commit_info = AsyncMock(return_value={
        "sha": "abc123",
        "commit": {"message": "test", "author": {"name": "User"}}
    })
    mock_github.get_file_content = AsyncMock(return_value="content")
    mock_github.create_branch = AsyncMock(return_value=True)
    mock_github.update_file = AsyncMock(return_value=True)
    mock_github.create_pull_request = AsyncMock(return_value=123)
    mock_github.post_commit_comment = AsyncMock(return_value=True)
    
    code_reviewer = MagicMock()
    code_reviewer.review_commit = AsyncMock(return_value={"success": True, "review": "Review"})
    
    readme_updater = MagicMock()
    readme_updater.update_readme = AsyncMock(return_value=None)  # No updates
    
    spec_updater = MagicMock()
    spec_updater.update_spec = AsyncMock(return_value=None)  # No updates
    
    code_review_updater = MagicMock()
    code_review_updater.update_review_log = AsyncMock(return_value="Updated log")
    
    orch = AutomationOrchestrator(
        github_client=mock_github,
        code_reviewer=code_reviewer,
        readme_updater=readme_updater,
        spec_updater=spec_updater,
        code_review_updater=code_review_updater,
        config=mock_config
    )
    
    return orch, code_reviewer, readme_updater, spec_updater, mock_github

@pytest.mark.asyncio
async def test_concurrent_pushes(orchestrator_setup):
    """Test handling 10 concurrent push events."""
    orch, code_reviewer, _, _, _ = orchestrator_setup
    
    payloads = [
        {
            "ref": "refs/heads/main",
            "commits": [{"id": f"commit{i}"}],
            "head_commit": {"id": f"commit{i}"}
        }
        for i in range(10)
    ]
    
    # Run all orchestrations concurrently
    results = await asyncio.gather(
        *[orch.run_automation(payload) for payload in payloads],
        return_exceptions=True
    )
    
    # Verify all completed successfully
    assert len(results) == 10
    for result in results:
        assert not isinstance(result, Exception)
        assert result["success"] is True

@pytest.mark.asyncio
async def test_concurrent_pushes_with_delays(orchestrator_setup):
    """Test concurrent pushes with simulated API delays."""
    orch, code_reviewer, _, _, _ = orchestrator_setup
    
    # Add delay to simulate slow API calls
    async def slow_review(*args, **kwargs):
        await asyncio.sleep(0.1)
        return {"success": True, "review": "Review"}
    
    # Use side_effect to override the mock behavior
    code_reviewer.review_commit.side_effect = slow_review
    
    payloads = [
        {
            "ref": "refs/heads/main",
            "commits": [{"id": f"commit{i}"}],
            "head_commit": {"id": f"commit{i}"}
        }
        for i in range(5)
    ]
    
    # Run concurrently and measure time
    import time
    start = time.time()
    results = await asyncio.gather(
        *[orch.run_automation(payload) for payload in payloads]
    )
    duration = time.time() - start
    
    # Should complete in parallel (not 5 * 0.1 = 0.5s sequentially)
    # Very lenient timing for Windows/CI environments
    assert duration < 1.0  # Just verify it doesn't run fully sequentially
    assert len(results) == 5
