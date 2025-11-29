import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from automation_agent.llm_client import LLMClient
import os

@pytest.fixture
def mock_env_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")

@pytest.fixture
def mock_env_anthropic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_anthropic_key")

@pytest.mark.asyncio
async def test_init_openai_success(mock_env_openai, mock_openai_client):
    with patch("openai.AsyncOpenAI", return_value=mock_openai_client):
        client = LLMClient(provider="openai")
        assert client.provider == "openai"
        assert client.api_key == "test_openai_key"
        assert client._client == mock_openai_client

@pytest.mark.asyncio
async def test_init_anthropic_success(mock_env_anthropic, mock_anthropic_client):
    with patch("anthropic.AsyncAnthropic", return_value=mock_anthropic_client):
        client = LLMClient(provider="anthropic")
        assert client.provider == "anthropic"
        assert client.api_key == "test_anthropic_key"
        assert client._client == mock_anthropic_client

def test_init_invalid_provider():
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        LLMClient(provider="invalid")

def test_init_missing_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OpenAI API key not provided"):
        LLMClient(provider="openai")

@pytest.mark.asyncio
async def test_generate_openai(mock_env_openai, mock_openai_client):
    with patch("openai.AsyncOpenAI", return_value=mock_openai_client):
        client = LLMClient(provider="openai")
        response = await client.generate("Test prompt")
        assert response == "Mocked OpenAI response"
        mock_openai_client.chat.completions.create.assert_called_once()
        args = mock_openai_client.chat.completions.create.call_args[1]
        assert args["messages"][0]["content"] == "Test prompt"

@pytest.mark.asyncio
async def test_generate_anthropic(mock_env_anthropic, mock_anthropic_client):
    with patch("anthropic.AsyncAnthropic", return_value=mock_anthropic_client):
        client = LLMClient(provider="anthropic")
        response = await client.generate("Test prompt")
        assert response == "Mocked Anthropic response"
        mock_anthropic_client.messages.create.assert_called_once()
        args = mock_anthropic_client.messages.create.call_args[1]
        assert args["messages"][0]["content"] == "Test prompt"

@pytest.mark.asyncio
async def test_generate_failure(mock_env_openai, mock_openai_client):
    mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
    with patch("openai.AsyncOpenAI", return_value=mock_openai_client):
        client = LLMClient(provider="openai")
        with pytest.raises(Exception, match="API Error"):
            await client.generate("Test prompt")

@pytest.mark.asyncio
async def test_analyze_code(mock_env_openai, mock_openai_client):
    with patch("openai.AsyncOpenAI", return_value=mock_openai_client):
        client = LLMClient(provider="openai")
        diff = "diff --git a/file.py b/file.py\n+new line"
        response = await client.analyze_code(diff)
        assert response == "Mocked OpenAI response"
        # Verify prompt contains diff
        call_args = mock_openai_client.chat.completions.create.call_args[1]
        assert diff in call_args["messages"][0]["content"]

@pytest.mark.asyncio
async def test_analyze_code_truncated(mock_env_openai, mock_openai_client):
    with patch("openai.AsyncOpenAI", return_value=mock_openai_client):
        client = LLMClient(provider="openai")
        long_diff = "a" * 10000
        await client.analyze_code(long_diff)
        call_args = mock_openai_client.chat.completions.create.call_args[1]
        assert "truncated" in call_args["messages"][0]["content"]

@pytest.mark.asyncio
async def test_update_readme(mock_env_openai, mock_openai_client):
    with patch("openai.AsyncOpenAI", return_value=mock_openai_client):
        client = LLMClient(provider="openai")
        diff = "diff content"
        readme = "# Old Readme"
        response = await client.update_readme(diff, readme)
        assert response == "Mocked OpenAI response"
        call_args = mock_openai_client.chat.completions.create.call_args[1]
        assert diff in call_args["messages"][0]["content"]
        assert readme in call_args["messages"][0]["content"]

@pytest.mark.asyncio
async def test_update_spec(mock_env_openai, mock_openai_client):
    with patch("openai.AsyncOpenAI", return_value=mock_openai_client):
        client = LLMClient(provider="openai")
        commit_info = {"message": "feat: new feature"}
        spec = "# Old Spec"
        response = await client.update_spec(commit_info, spec)
        assert response == "Mocked OpenAI response"
        call_args = mock_openai_client.chat.completions.create.call_args[1]
        assert "feat: new feature" in call_args["messages"][0]["content"]
        assert spec in call_args["messages"][0]["content"]
@pytest.fixture
def mock_env_gemini(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key")

@pytest.mark.asyncio
async def test_init_gemini_success(mock_env_gemini):
    with patch("google.generativeai.configure") as mock_configure, \
         patch("google.generativeai.GenerativeModel") as mock_model_cls:
        
        client = LLMClient(provider="gemini")
        assert client.provider == "gemini"
        assert client.api_key == "test_gemini_key"
        mock_configure.assert_called_once_with(api_key="test_gemini_key")
        mock_model_cls.assert_called_once_with("gemini-2.0-flash")

@pytest.mark.asyncio
async def test_generate_gemini(mock_env_gemini):
    with patch("google.generativeai.configure"), \
         patch("google.generativeai.GenerativeModel") as mock_model_cls:
        
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Mocked Gemini response"
        # Mock async generate_content_async
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_model_cls.return_value = mock_model

        client = LLMClient(provider="gemini")
        response = await client.generate("Test prompt")
        
        assert response == "Mocked Gemini response"
        mock_model.generate_content_async.assert_called_once()
        args = mock_model.generate_content_async.call_args
        assert args[0][0] == "Test prompt"
        assert args[1]["generation_config"]["max_output_tokens"] == 1000
