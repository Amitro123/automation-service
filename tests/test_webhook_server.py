import unittest
import pytest
import json
import hashlib
import hmac
from flask import request
from unittest.mock import MagicMock, patch, AsyncMock
from src.automation_agent.webhook_server import WebhookServer
from src.automation_agent.config import Config


class TestWebhookServerSync(unittest.TestCase):
    """Synchronous tests for WebhookServer."""

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
             patch('src.automation_agent.webhook_server.CodeReviewUpdater'), \
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

    @patch('src.automation_agent.webhook_server.threading.Thread')
    def test_webhook_push_event(self, mock_thread):
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

        response = self.app.post('/webhook', headers=headers, data=data)
        
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json['status'], 'accepted')
        mock_thread.assert_called_once()
        
        # Verify thread was started with correct target
        call_args = mock_thread.call_args
        self.assertEqual(call_args[1]['target'], self.server._run_background_task)
        self.assertEqual(call_args[1]['args'][0], payload)

    @patch('src.automation_agent.webhook_server.asyncio.run')
    def test_run_background_task(self, mock_asyncio_run):
        payload = {"commits": [{"id": "sha1"}]}
        
        # Mock _handle_push_event to be a coroutine
        async def mock_handle(p):
            pass
            
        with patch.object(self.server, '_handle_push_event', side_effect=mock_handle) as mock_method:
            self.server._run_background_task(payload)
            
            mock_asyncio_run.assert_called_once()
            # We can't easily verify the coroutine passed to run() is exactly what we expect 
            # without more complex mocking, but we verify run() is called.

    @patch('src.automation_agent.webhook_server.asyncio.run')
    def test_run_background_task_exception(self, mock_asyncio_run):
        mock_asyncio_run.side_effect = Exception("Error")
        payload = {"commits": [{"id": "sha1"}]}
        
        # Should not raise exception (logged only)
        self.server._run_background_task(payload)

    def test_verify_signature_missing_header(self):
        with self.server.app.test_request_context('/webhook', headers={}):
            self.assertFalse(self.server._verify_signature(request))

    def test_verify_signature_invalid_format(self):
        with self.server.app.test_request_context('/webhook', headers={'X-Hub-Signature-256': 'invalid_format'}):
            self.assertFalse(self.server._verify_signature(request))

    def test_verify_signature_wrong_algorithm(self):
        with self.server.app.test_request_context('/webhook', headers={'X-Hub-Signature-256': 'sha1=123'}):
            self.assertFalse(self.server._verify_signature(request))


# Async tests - standalone pytest functions (not in unittest.TestCase)
@pytest.fixture
def webhook_server():
    """Create a WebhookServer instance with mocked dependencies."""
    config = MagicMock(spec=Config)
    config.GITHUB_TOKEN = "token"
    config.GITHUB_WEBHOOK_SECRET = "secret"
    config.REPOSITORY_OWNER = "owner"
    config.REPOSITORY_NAME = "repo"
    config.LLM_PROVIDER = "openai"
    config.OPENAI_API_KEY = "key"
    config.HOST = "0.0.0.0"
    config.PORT = 8080
    config.DEBUG = False

    with patch('src.automation_agent.webhook_server.GitHubClient'), \
         patch('src.automation_agent.webhook_server.LLMClient'), \
         patch('src.automation_agent.webhook_server.CodeReviewer'), \
         patch('src.automation_agent.webhook_server.ReadmeUpdater'), \
         patch('src.automation_agent.webhook_server.SpecUpdater'), \
         patch('src.automation_agent.webhook_server.CodeReviewUpdater'), \
         patch('src.automation_agent.webhook_server.AutomationOrchestrator'):
        server = WebhookServer(config)
        yield server


@pytest.mark.asyncio
async def test_handle_push_event_success(webhook_server):
    """Test successful push event handling."""
    payload = {"commits": [{"id": "sha1"}]}
    webhook_server.orchestrator.run_automation = AsyncMock(return_value={"success": True})
    
    await webhook_server._handle_push_event(payload)
    
    webhook_server.orchestrator.run_automation.assert_called_once_with(payload)


@pytest.mark.asyncio
async def test_handle_push_event_no_commits(webhook_server):
    """Test push event with no commits."""
    payload = {"commits": []}
    webhook_server.orchestrator.run_automation = AsyncMock()
    
    await webhook_server._handle_push_event(payload)
    
    webhook_server.orchestrator.run_automation.assert_not_called()


@pytest.mark.asyncio
async def test_handle_push_event_exception(webhook_server):
    """Test push event handling with exception."""
    payload = {"commits": [{"id": "sha1"}]}
    webhook_server.orchestrator.run_automation = AsyncMock(side_effect=Exception("Error"))
    
    # Should not raise exception
    await webhook_server._handle_push_event(payload)
