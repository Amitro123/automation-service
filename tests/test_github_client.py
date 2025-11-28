import pytest
import requests
import base64
from unittest.mock import MagicMock, ANY

def test_get_commit_diff_success(github_client, mock_session):
    mock_response = MagicMock()
    mock_response.text = "diff content"
    mock_response.raise_for_status.return_value = None
    mock_session.get.return_value = mock_response

    diff = github_client.get_commit_diff("sha123")
    assert diff == "diff content"
    mock_session.get.assert_called_with(
        "https://api.github.com/repos/test_owner/test_repo/commits/sha123",
        headers={"Accept": "application/vnd.github.v3.diff"}
    )

def test_get_commit_diff_failure(github_client, mock_session):
    mock_session.get.side_effect = requests.exceptions.RequestException("Error")
    diff = github_client.get_commit_diff("sha123")
    assert diff is None

def test_get_commit_info_success(github_client, mock_session):
    mock_response = MagicMock()
    mock_response.json.return_value = {"sha": "sha123", "message": "msg"}
    mock_response.raise_for_status.return_value = None
    mock_session.get.return_value = mock_response

    info = github_client.get_commit_info("sha123")
    assert info["sha"] == "sha123"

def test_get_commit_info_failure(github_client, mock_session):
    mock_session.get.side_effect = requests.exceptions.RequestException("Error")
    info = github_client.get_commit_info("sha123")
    assert info is None

def test_post_commit_comment_success(github_client, mock_session):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_session.post.return_value = mock_response

    result = github_client.post_commit_comment("sha123", "comment")
    assert result is True
    mock_session.post.assert_called_with(
        "https://api.github.com/repos/test_owner/test_repo/commits/sha123/comments",
        json={"body": "comment"}
    )

def test_post_commit_comment_failure(github_client, mock_session):
    mock_session.post.side_effect = requests.exceptions.RequestException("Error")
    result = github_client.post_commit_comment("sha123", "comment")
    assert result is False

def test_create_issue_success(github_client, mock_session):
    mock_response = MagicMock()
    mock_response.json.return_value = {"number": 10}
    mock_response.raise_for_status.return_value = None
    mock_session.post.return_value = mock_response

    issue_num = github_client.create_issue("Title", "Body", ["label"])
    assert issue_num == 10
    mock_session.post.assert_called_with(
        "https://api.github.com/repos/test_owner/test_repo/issues",
        json={"title": "Title", "body": "Body", "labels": ["label"]}
    )

def test_create_issue_failure(github_client, mock_session):
    mock_session.post.side_effect = requests.exceptions.RequestException("Error")
    issue_num = github_client.create_issue("Title", "Body")
    assert issue_num is None

def test_get_file_content_success(github_client, mock_session):
    content = "hello world"
    encoded = base64.b64encode(content.encode()).decode()
    mock_response = MagicMock()
    mock_response.json.return_value = {"content": encoded}
    mock_response.raise_for_status.return_value = None
    mock_session.get.return_value = mock_response

    result = github_client.get_file_content("path/to/file")
    assert result == "hello world"

def test_get_file_content_404(github_client, mock_session):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_session.get.return_value = mock_response

    result = github_client.get_file_content("path/to/file")
    assert result is None

def test_get_file_content_failure(github_client, mock_session):
    mock_session.get.side_effect = requests.exceptions.RequestException("Error")
    result = github_client.get_file_content("path/to/file")
    assert result is None

def test_update_file_success(github_client, mock_session):
    # Mock get (check existence) - returns 404 (new file)
    mock_get_response = MagicMock()
    mock_get_response.status_code = 404
    
    # Mock put (update)
    mock_put_response = MagicMock()
    mock_put_response.raise_for_status.return_value = None
    
    mock_session.get.return_value = mock_get_response
    mock_session.put.return_value = mock_put_response

    result = github_client.update_file("file.txt", "content", "msg")
    assert result is True
    mock_session.put.assert_called_once()

def test_update_file_existing(github_client, mock_session):
    # Mock get (check existence) - returns 200 (existing file)
    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.json.return_value = {"sha": "old_sha"}
    
    # Mock put (update)
    mock_put_response = MagicMock()
    mock_put_response.raise_for_status.return_value = None
    
    mock_session.get.return_value = mock_get_response
    mock_session.put.return_value = mock_put_response

    result = github_client.update_file("file.txt", "content", "msg")
    assert result is True
    
    # Verify SHA was included in payload
    args, kwargs = mock_session.put.call_args
    assert kwargs["json"]["sha"] == "old_sha"

def test_update_file_failure(github_client, mock_session):
    mock_session.put.side_effect = requests.exceptions.RequestException("Error")
    result = github_client.update_file("file.txt", "content", "msg")
    assert result is False

def test_create_branch_success(github_client, mock_session):
    # Mock get ref
    mock_get_response = MagicMock()
    mock_get_response.json.return_value = {"object": {"sha": "base_sha"}}
    mock_get_response.raise_for_status.return_value = None
    
    # Mock create ref
    mock_post_response = MagicMock()
    mock_post_response.raise_for_status.return_value = None
    
    mock_session.get.return_value = mock_get_response
    mock_session.post.return_value = mock_post_response

    result = github_client.create_branch("new-branch")
    assert result is True
    mock_session.post.assert_called_with(
        "https://api.github.com/repos/test_owner/test_repo/git/refs",
        json={"ref": "refs/heads/new-branch", "sha": "base_sha"}
    )

def test_create_branch_failure(github_client, mock_session):
    mock_session.get.side_effect = requests.exceptions.RequestException("Error")
    result = github_client.create_branch("new-branch")
    assert result is False

def test_create_pull_request_success(github_client, mock_session):
    mock_response = MagicMock()
    mock_response.json.return_value = {"number": 123}
    mock_response.raise_for_status.return_value = None
    mock_session.post.return_value = mock_response

    pr_num = github_client.create_pull_request("Title", "Body", "head")
    assert pr_num == 123

def test_create_pull_request_failure(github_client, mock_session):
    mock_session.post.side_effect = requests.exceptions.RequestException("Error")
    pr_num = github_client.create_pull_request("Title", "Body", "head")
    assert pr_num is None

def test_get_recent_commits_success(github_client, mock_session):
    mock_response = MagicMock()
    mock_response.json.return_value = [{"sha": "1"}, {"sha": "2"}]
    mock_response.raise_for_status.return_value = None
    mock_session.get.return_value = mock_response

    commits = github_client.get_recent_commits(2)
    assert len(commits) == 2

def test_get_recent_commits_failure(github_client, mock_session):
    mock_session.get.side_effect = requests.exceptions.RequestException("Error")
    commits = github_client.get_recent_commits()
    assert commits == []
