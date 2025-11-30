import pytest
from unittest.mock import MagicMock, AsyncMock
from automation_agent.config import Config
from automation_agent.github_client import GitHubClient
from automation_agent.code_reviewer import CodeReviewer
from automation_agent.readme_updater import ReadmeUpdater
from automation_agent.spec_updater import SpecUpdater
from automation_agent.code_review_updater import CodeReviewUpdater
from automation_agent.llm_client import LLMClient

@pytest.fixture
def mock_config():
    config = MagicMock(spec=Config)
    config.POST_REVIEW_AS_ISSUE = False
    config.CREATE_PR = True
    config.AUTO_COMMIT = False
    return config

@pytest.fixture
def mock_github_client():
    return AsyncMock(spec=GitHubClient)

@pytest.fixture
def mock_code_reviewer():
    return MagicMock(spec=CodeReviewer)

@pytest.fixture
def mock_readme_updater():
    return MagicMock(spec=ReadmeUpdater)

@pytest.fixture
def mock_spec_updater():
    return MagicMock(spec=SpecUpdater)

@pytest.fixture
def mock_code_review_updater():
    return MagicMock(spec=CodeReviewUpdater)

@pytest.fixture
def mock_session():
    """Mock requests session."""
    session = MagicMock()
    return session

@pytest.fixture
def github_client(mock_session):
    """Real GitHubClient with mocked session."""
    client = GitHubClient(token="test_token", owner="test_owner", repo="test_repo")
    client.session = mock_session
    return client

@pytest.fixture
def mock_openai_client():
    """Mock AsyncOpenAI client."""
    client = AsyncMock()
    # Mock chat.completions.create
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Mocked OpenAI response"))]
    client.chat.completions.create.return_value = mock_response
    return client

@pytest.fixture
def mock_anthropic_client():
    """Mock AsyncAnthropic client."""
    client = AsyncMock()
    # Mock messages.create
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Mocked Anthropic response")]
    client.messages.create.return_value = mock_response
    return client

@pytest.fixture
def mock_llm_client():
    """Mock LLMClient."""
    client = AsyncMock(spec=LLMClient)
    client.analyze_code.return_value = "Mocked code analysis"
    client.update_readme.return_value = "Mocked README update"
    client.update_spec.return_value = "Mocked spec update"
    return client
