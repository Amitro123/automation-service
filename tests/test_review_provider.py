import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.automation_agent.review_provider import JulesReviewProvider, LLMReviewProvider
from src.automation_agent.config import Config

@pytest.fixture
def mock_config():
    config = MagicMock(spec=Config)
    config.JULES_API_KEY = "test_key"
    config.JULES_API_URL = "https://test.api/review"
    config.JULES_SOURCE_ID = "sources/github/test/repo"
    config.JULES_PROJECT_ID = "test-project"
    return config

@pytest.fixture
def mock_fallback_provider():
    provider = MagicMock(spec=LLMReviewProvider)
    provider.review_code = AsyncMock(return_value=("Fallback Review", {"provider": "llm"}))
    provider.update_readme = AsyncMock(return_value=("Fallback Readme", {}))
    provider.update_spec = AsyncMock(return_value=("Fallback Spec", {}))
    return provider

@pytest.mark.asyncio
async def test_jules_review_success(mock_config, mock_fallback_provider):
    provider = JulesReviewProvider(mock_config, mock_fallback_provider)
    
    with patch("aiohttp.ClientSession") as MockSession:
        mock_session = AsyncMock()
        MockSession.return_value.__aenter__.return_value = mock_session

        # Mock POST response (session creation)
        mock_post_response = AsyncMock()
        mock_post_response.status = 200
        mock_post_response.json.return_value = {"id": "session-123"}

        # Set up post context manager
        mock_post_ctx = MagicMock()
        mock_post_ctx.__aenter__ = AsyncMock(return_value=mock_post_response)
        mock_post_ctx.__aexit__ = AsyncMock(return_value=None)
        mock_session.post = MagicMock(return_value=mock_post_ctx)

        # Mock GET response (polling)
        mock_get_response = AsyncMock()
        mock_get_response.status = 200
        # First poll: RUNNING, Second: COMPLETED
        mock_get_response.json.side_effect = [
            {"state": "RUNNING"},
            {"state": "COMPLETED", "outputs": [{"text": "Jules Review Content"}]}
        ]

        # Set up get context manager
        mock_get_ctx = MagicMock()
        mock_get_ctx.__aenter__ = AsyncMock(return_value=mock_get_response)
        mock_get_ctx.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_get_ctx)
        
        review, metadata = await provider.review_code("diff")
        
        assert "Jules Review Content" in review
        assert "Jules / Google Code Review API" in review
        assert metadata.get("provider") == "jules"
        assert metadata.get("session_id") == "session-123"
        
        # Verify calls
        assert mock_session.post.called
        assert mock_session.get.call_count == 2
        
        mock_fallback_provider.review_code.assert_not_called()

@pytest.mark.asyncio
async def test_jules_review_failure_fallback(mock_config, mock_fallback_provider):
    provider = JulesReviewProvider(mock_config, mock_fallback_provider)
    
    with patch("aiohttp.ClientSession") as MockSession:
        mock_session = AsyncMock()
        MockSession.return_value.__aenter__.return_value = mock_session

        # Mock POST response (session creation) failure
        mock_post_response = AsyncMock()
        mock_post_response.status = 500
        mock_post_response.text.return_value = "Internal Server Error"

        mock_post_ctx = MagicMock()
        mock_post_ctx.__aenter__ = AsyncMock(return_value=mock_post_response)
        mock_post_ctx.__aexit__ = AsyncMock(return_value=None)
        mock_session.post = MagicMock(return_value=mock_post_ctx)
        
        review, metadata = await provider.review_code("diff")
        
        assert review == "Fallback Review"
        mock_fallback_provider.review_code.assert_called_once_with("diff", "")  # Now includes past_lessons

@pytest.mark.asyncio
async def test_jules_review_exception_fallback(mock_config, mock_fallback_provider):
    provider = JulesReviewProvider(mock_config, mock_fallback_provider)
    
    with patch("aiohttp.ClientSession") as MockSession:
        mock_session = AsyncMock()
        MockSession.return_value.__aenter__.return_value = mock_session

        mock_session.post = MagicMock(side_effect=Exception("Network Error"))

        review, metadata = await provider.review_code("diff")
        
        assert review == "Fallback Review"
        mock_fallback_provider.review_code.assert_called_once_with("diff", "")  # Now includes past_lessons

@pytest.mark.asyncio
async def test_jules_update_readme_fallback(mock_config, mock_fallback_provider):
    provider = JulesReviewProvider(mock_config, mock_fallback_provider)
    
    result, metadata = await provider.update_readme("diff", "readme")
    
    assert result == "Fallback Readme"
    mock_fallback_provider.update_readme.assert_called_once_with("diff", "readme", "")

@pytest.mark.asyncio
async def test_jules_update_spec_fallback(mock_config, mock_fallback_provider):
    provider = JulesReviewProvider(mock_config, mock_fallback_provider)
    
    result, metadata = await provider.update_spec({}, "diff", "spec")
    
    assert result == "Fallback Spec"
    mock_fallback_provider.update_spec.assert_called_once_with({}, "diff", "spec", "")
