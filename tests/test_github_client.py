import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import httpx
import base64
from src.automation_agent.github_client import GitHubClient

@pytest.fixture
def github_client():
    return GitHubClient("token", "test_owner", "test_repo")

@pytest.fixture
def mock_httpx_client():
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        yield mock_client

@pytest.mark.asyncio
async def test_get_commit_diff_success(github_client, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.text = "diff content"
    mock_response.raise_for_status.return_value = None
    mock_httpx_client.get.return_value = mock_response

    diff = await github_client.get_commit_diff("sha123")
    assert diff == "diff content"
    mock_httpx_client.get.assert_called_with(
        "https://api.github.com/repos/test_owner/test_repo/commits/sha123",
        headers={**github_client.headers, "Accept": "application/vnd.github.v3.diff"}
    )

@pytest.mark.asyncio
async def test_get_commit_diff_failure(github_client, mock_httpx_client):
    mock_httpx_client.get.side_effect = httpx.HTTPError("Error")
    diff = await github_client.get_commit_diff("sha123")
    assert diff is None

@pytest.mark.asyncio
async def test_get_commit_info_success(github_client, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"sha": "sha123", "message": "msg"}
    mock_response.raise_for_status.return_value = None
    mock_httpx_client.get.return_value = mock_response

    info = await github_client.get_commit_info("sha123")
    assert info["sha"] == "sha123"

@pytest.mark.asyncio
async def test_get_commit_info_failure(github_client, mock_httpx_client):
    mock_httpx_client.get.side_effect = httpx.HTTPError("Error")
    info = await github_client.get_commit_info("sha123")
    assert info is None

@pytest.mark.asyncio
async def test_post_commit_comment_success(github_client, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_httpx_client.post.return_value = mock_response

    result = await github_client.post_commit_comment("sha123", "comment")
    assert result is True
    mock_httpx_client.post.assert_called_with(
        "https://api.github.com/repos/test_owner/test_repo/commits/sha123/comments",
        json={"body": "comment"}
    )

@pytest.mark.asyncio
async def test_post_commit_comment_failure(github_client, mock_httpx_client):
    mock_httpx_client.post.side_effect = httpx.HTTPError("Error")
    result = await github_client.post_commit_comment("sha123", "comment")
    assert result is False

@pytest.mark.asyncio
async def test_create_issue_success(github_client, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"number": 10}
    mock_response.raise_for_status.return_value = None
    mock_httpx_client.post.return_value = mock_response

    issue_num = await github_client.create_issue("Title", "Body", ["label"])
    assert issue_num == 10
    mock_httpx_client.post.assert_called_with(
        "https://api.github.com/repos/test_owner/test_repo/issues",
        json={"title": "Title", "body": "Body", "labels": ["label"]}
    )

@pytest.mark.asyncio
async def test_create_issue_failure(github_client, mock_httpx_client):
    mock_httpx_client.post.side_effect = httpx.HTTPError("Error")
    issue_num = await github_client.create_issue("Title", "Body")
    assert issue_num is None

@pytest.mark.asyncio
async def test_get_file_content_success(github_client, mock_httpx_client):
    content = "hello world"
    encoded = base64.b64encode(content.encode()).decode()
    mock_response = MagicMock()
    mock_response.json.return_value = {"content": encoded}
    mock_response.raise_for_status.return_value = None
    mock_httpx_client.get.return_value = mock_response

    result = await github_client.get_file_content("path/to/file")
    assert result == "hello world"

@pytest.mark.asyncio
async def test_get_file_content_404(github_client, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_httpx_client.get.return_value = mock_response

    result = await github_client.get_file_content("path/to/file")
    assert result is None

@pytest.mark.asyncio
async def test_get_file_content_failure(github_client, mock_httpx_client):
    mock_httpx_client.get.side_effect = httpx.HTTPError("Error")
    result = await github_client.get_file_content("path/to/file")
    assert result is None

@pytest.mark.asyncio
async def test_update_file_success(github_client, mock_httpx_client):
    # Mock get (check existence) - returns 404 (new file)
    mock_get_response = MagicMock()
    mock_get_response.status_code = 404
    
    # Mock put (update)
    mock_put_response = MagicMock()
    mock_put_response.raise_for_status.return_value = None
    
    mock_httpx_client.get.return_value = mock_get_response
    mock_httpx_client.put.return_value = mock_put_response

    result = await github_client.update_file("file.txt", "content", "msg")
    assert result is True
    mock_httpx_client.put.assert_called_once()

@pytest.mark.asyncio
async def test_update_file_existing(github_client, mock_httpx_client):
    # Mock get (check existence) - returns 200 (existing file)
    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.json.return_value = {"sha": "old_sha"}
    
    # Mock put (update)
    mock_put_response = MagicMock()
    mock_put_response.raise_for_status.return_value = None
    
    mock_httpx_client.get.return_value = mock_get_response
    mock_httpx_client.put.return_value = mock_put_response

    result = await github_client.update_file("file.txt", "content", "msg")
    assert result is True
    
    # Verify SHA was included in payload
    _, kwargs = mock_httpx_client.put.call_args
    assert kwargs["json"]["sha"] == "old_sha"
@pytest.mark.asyncio
async def test_update_file_failure(github_client, mock_httpx_client):
    mock_httpx_client.put.side_effect = httpx.HTTPError("Error")
    result = await github_client.update_file("file.txt", "content", "msg")
    assert result is False

@pytest.mark.asyncio
async def test_create_branch_success(github_client, mock_httpx_client):
    # Mock get ref
    mock_get_response = MagicMock()
    mock_get_response.json.return_value = {"object": {"sha": "base_sha"}}
    mock_get_response.raise_for_status.return_value = None
    
    # Mock create ref
    mock_post_response = MagicMock()
    mock_post_response.raise_for_status.return_value = None
    
    mock_httpx_client.get.return_value = mock_get_response
    mock_httpx_client.post.return_value = mock_post_response

    result = await github_client.create_branch("new-branch")
    assert result is True
    mock_httpx_client.post.assert_called_with(
        "https://api.github.com/repos/test_owner/test_repo/git/refs",
        json={"ref": "refs/heads/new-branch", "sha": "base_sha"}
    )

@pytest.mark.asyncio
async def test_create_branch_failure(github_client, mock_httpx_client):
    mock_httpx_client.get.side_effect = httpx.HTTPError("Error")
    result = await github_client.create_branch("new-branch")
    assert result is False

@pytest.mark.asyncio
async def test_create_pull_request_success(github_client, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"number": 123}
    mock_response.raise_for_status.return_value = None
    mock_httpx_client.post.return_value = mock_response

    pr_num = await github_client.create_pull_request("Title", "Body", "head")
    assert pr_num == 123

@pytest.mark.asyncio
async def test_create_pull_request_failure(github_client, mock_httpx_client):
    mock_httpx_client.post.side_effect = httpx.HTTPError("Error")
    pr_num = await github_client.create_pull_request("Title", "Body", "head")
    assert pr_num is None

@pytest.mark.asyncio
async def test_get_recent_commits_success(github_client, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.json.return_value = [{"sha": "1"}, {"sha": "2"}]
    mock_response.raise_for_status.return_value = None
    mock_httpx_client.get.return_value = mock_response

    commits = await github_client.get_recent_commits(2)
    assert len(commits) == 2

@pytest.mark.asyncio
async def test_get_recent_commits_failure(github_client, mock_httpx_client):
    mock_httpx_client.get.side_effect = httpx.HTTPError("Error")
    commits = await github_client.get_recent_commits()
    assert commits == []
