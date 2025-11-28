import unittest
from unittest.mock import MagicMock, patch
from src.automation_agent.github_client import GitHubClient

class TestGitHubClient(unittest.TestCase):

    def setUp(self):
        self.client = GitHubClient("token", "owner", "repo")
        self.client.session = MagicMock()

    def test_get_commit_diff(self):
        self.client.session.get.return_value.status_code = 200
        self.client.session.get.return_value.text = "diff content"

        diff = self.client.get_commit_diff("sha")
        self.assertEqual(diff, "diff content")
        self.client.session.get.assert_called()

    def test_post_commit_comment(self):
        self.client.session.post.return_value.status_code = 201

        result = self.client.post_commit_comment("sha", "comment")
        self.assertTrue(result)
        self.client.session.post.assert_called()

    def test_create_issue(self):
        self.client.session.post.return_value.status_code = 201
        self.client.session.post.return_value.json.return_value = {"number": 123}

        issue_number = self.client.create_issue("title", "body")
        self.assertEqual(issue_number, 123)

    def test_get_file_content(self):
        import base64
        content = "file content"
        b64_content = base64.b64encode(content.encode()).decode()

        self.client.session.get.return_value.status_code = 200
        self.client.session.get.return_value.json.return_value = {"content": b64_content}

        result = self.client.get_file_content("path")
        self.assertEqual(result, "file content")
