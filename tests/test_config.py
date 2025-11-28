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
            "LLM_PROVIDER": "openai"
        }):
            # Reload config to pick up env vars
            # Since Config properties are class attributes loaded at import time,
            # we need to mock the class attributes or reload the module.
            # However, the validate method checks the class attributes.
            # Let's mock the attributes directly on the class for the test.

            Config.GITHUB_TOKEN = "token"
            Config.GITHUB_WEBHOOK_SECRET = "secret"
            Config.REPOSITORY_OWNER = "owner"
            Config.REPOSITORY_NAME = "repo"
            Config.OPENAI_API_KEY = "key"
            Config.LLM_PROVIDER = "openai"

            errors = Config.validate()
            self.assertEqual(errors, [])

    def test_validate_failure(self):
        Config.GITHUB_TOKEN = ""
        errors = Config.validate()
        self.assertIn("GITHUB_TOKEN is required", errors)

    def test_get_repo_full_name(self):
        Config.REPOSITORY_OWNER = "owner"
        Config.REPOSITORY_NAME = "repo"
        self.assertEqual(Config.get_repo_full_name(), "owner/repo")
