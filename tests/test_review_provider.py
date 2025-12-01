import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from automation_agent.review_provider import JulesReviewProvider, LLMReviewProvider
from automation_agent.config import Config

@pytest.fixture
def mock_config():
    config = MagicMock(spec=Config)
    config.JULES_API_KEY = "test_key"
    config.JULES_API_URL = "https://test.api/review"
    return config

@pytest.fixture
def mock_fallback_provider():
    provider = MagicMock(spec=LLMReviewProvider)
    provider.review_code = AsyncMock(return_value="Fallback Review")
    provider.update_readme = AsyncMock(return_value="Fallback Readme")
    provider.update_spec = AsyncMock(return_value="Fallback Spec")
    return provider

@pytest.mark.asyncio
async def test_jules_review_success(mock_config, mock_fallback_provider):
    provider = JulesReviewProvider(mock_config, mock_fallback_provider)
    
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"review": "Jules Review Content"}
        mock_post.return_value.__aenter__.return_value = mock_response
        
        review = await provider.review_code("diff")
        
        assert "Jules Review Content" in review
        assert "Jules / Google Code Review API" in review
        
        # Verify timeout was passed
        args, kwargs = mock_post.call_args
        assert "timeout" in kwargs
        assert kwargs["timeout"].total == 30
        
        mock_fallback_provider.review_code.assert_not_called()

@pytest.mark.asyncio
async def test_jules_review_failure_fallback(mock_config, mock_fallback_provider):
    provider = JulesReviewProvider(mock_config, mock_fallback_provider)
    
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text.return_value = "Internal Server Error"
        mock_post.return_value.__aenter__.return_value = mock_response
        
        review = await provider.review_code("diff")
        
        assert review == "Fallback Review"
        mock_fallback_provider.review_code.assert_called_once_with("diff")

@pytest.mark.asyncio
async def test_jules_review_exception_fallback(mock_config, mock_fallback_provider):
    provider = JulesReviewProvider(mock_config, mock_fallback_provider)
    
    with patch("aiohttp.ClientSession.post", side_effect=Exception("Network Error")):
        review = await provider.review_code("diff")
        
        assert review == "Fallback Review"
        mock_fallback_provider.review_code.assert_called_once_with("diff")

@pytest.mark.asyncio
async def test_jules_update_readme_fallback(mock_config, mock_fallback_provider):
    provider = JulesReviewProvider(mock_config, mock_fallback_provider)
    
    result = await provider.update_readme("diff", "readme")
    
    assert result == "Fallback Readme"
    mock_fallback_provider.update_readme.assert_called_once_with("diff", "readme")

@pytest.mark.asyncio
async def test_jules_update_spec_fallback(mock_config, mock_fallback_provider):
    provider = JulesReviewProvider(mock_config, mock_fallback_provider)
    
    result = await provider.update_spec({}, "diff", "spec")
    
    assert result == "Fallback Spec"
    mock_fallback_provider.update_spec.assert_called_once_with({}, "diff", "spec")
