import unittest
import json
import hashlib
import hmac
from unittest.mock import MagicMock, patch
from src.automation_agent.webhook_server import WebhookServer
from src.automation_agent.config import Config

class TestWebhookServer(unittest.TestCase):

    def setUp(self):
        # Mock Config
        self.config = MagicMock(spec=Config)
        self.config.GITHUB_TOKEN = "token"
        self.config.GITHUB_WEBHOOK_SECRET = "secret"
        self.config.REPOSITORY_OWNER = "owner"
        self.config.REPOSITORY_NAME = "repo"
        self.config.LLM_PROVIDER = "openai"
        self.config.OPENAI_API_KEY = "key"
        self.config.HOST = "0.0.0.0"
        self.config.PORT = 8080
        self.config.DEBUG = False

        # Patch components initialization
        with patch('src.automation_agent.webhook_server.GitHubClient'), \
             patch('src.automation_agent.webhook_server.LLMClient'), \
             patch('src.automation_agent.webhook_server.CodeReviewer'), \
             patch('src.automation_agent.webhook_server.ReadmeUpdater'), \
             patch('src.automation_agent.webhook_server.SpecUpdater'), \
             patch('src.automation_agent.webhook_server.AutomationOrchestrator'):

            self.server = WebhookServer(self.config)
            self.app = self.server.app.test_client()

    def test_health_check(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'healthy')

    def test_webhook_invalid_signature(self):
        response = self.app.post('/webhook', headers={'X-Hub-Signature-256': 'invalid'})
        self.assertEqual(response.status_code, 403)

    def test_webhook_valid_signature_ping(self):
        # Calculate valid signature
        data = b'{}'
        mac = hmac.new(b'secret', msg=data, digestmod=hashlib.sha256)
        signature = f"sha256={mac.hexdigest()}"

        headers = {
            'X-Hub-Signature-256': signature,
            'X-GitHub-Event': 'ping'
        }

        response = self.app.post('/webhook', headers=headers, data=data)
        self.assertEqual(response.status_code, 200)

    def test_webhook_push_event(self):
        payload = {
            "ref": "refs/heads/main",
            "commits": [{"id": "sha1", "message": "test"}],
            "head_commit": {"id": "sha1", "message": "test"}
        }
        data = json.dumps(payload).encode()

        mac = hmac.new(b'secret', msg=data, digestmod=hashlib.sha256)
        signature = f"sha256={mac.hexdigest()}"

        headers = {
            'X-Hub-Signature-256': signature,
            'X-GitHub-Event': 'push',
            'Content-Type': 'application/json'
        }

        # Mock orchestrator
        self.server.orchestrator.process_push.return_value = {"success": True}

        response = self.app.post('/webhook', headers=headers, data=data)
        self.assertEqual(response.status_code, 200)
        self.server.orchestrator.process_push.assert_called_once()
