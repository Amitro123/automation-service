import unittest
import os
from unittest.mock import patch
from src.automation_agent.config import Config

class TestConfig(unittest.TestCase):

    def test_validate_success(self):
        with patch.dict(os.environ, {
            "GITHUB_TOKEN": "token",
            "GITHUB_WEBHOOK_SECRET": "secret",
            "REPOSITORY_OWNER": "owner",
            "REPOSITORY_NAME": "repo",
            "OPENAI_API_KEY": "key",
            "LLM_PROVIDER": "openai",
            "JULES_API_KEY": "jules_key",
            "JULES_SOURCE_ID": "source",
        }):
            # Clear any cached file config
            Config._file_config = {}
            errors = Config.validate()
            self.assertEqual(errors, [])

    def test_validate_failure(self):
        # Ensure environment is clean/missing keys
        with patch.dict(os.environ, {}, clear=True):
             Config._file_config = {} # correct way to clear cache
             errors = Config.validate()
             self.assertIn("GITHUB_TOKEN is required", errors)

    def test_get_repo_full_name(self):
        with patch.dict(os.environ, {
            "REPOSITORY_OWNER": "owner",
            "REPOSITORY_NAME": "repo"
        }):
            Config._file_config = {}
            self.assertEqual(Config.get_repo_full_name(), "owner/repo")
