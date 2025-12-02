"""Review provider abstraction for pluggable code review engines."""

import logging
import aiohttp
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from .llm_client import LLMClient, RateLimitError
from .config import Config

logger = logging.getLogger(__name__)


class ReviewProvider(ABC):
    """Abstract base class for code review providers."""

    @abstractmethod
    async def review_code(self, diff: str) -> Union[str, Dict[str, Any]]:
        """Analyze code changes and provide a review.
        
        Returns:
            str: Review content on success
            Dict[str, Any]: Error dict with success=False, error_type, message on failure
        """
        pass

    @abstractmethod
    async def update_readme(self, diff: str, current_readme: str) -> str:
        """Generate updates for README.md."""
        pass

    @abstractmethod
    async def update_spec(self, commit_info: Dict[str, Any], diff: str, current_spec: str) -> str:
        """Update spec.md based on commit info."""
        pass


class LLMReviewProvider(ReviewProvider):
    """Review provider using the existing LLMClient (Gemini/OpenAI/Anthropic)."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def review_code(self, diff: str) -> Union[str, Dict[str, Any]]:
        """Review code using LLM.
        
        Returns:
            str: Review content on success
            Dict[str, Any]: Error dict on rate limit or other failures
        """
        try:
            return await self.llm.analyze_code(diff)
        except RateLimitError as e:
            logger.exception("LLM review failed: Rate limit exceeded")
            return {
                "success": False,
                "error_type": "llm_rate_limited",
                "message": str(e)
            }
        except Exception as e:
            logger.exception("LLM review failed")
            return {
                "success": False,
                "error_type": "llm_error",
                "message": str(e)
            }

    async def update_readme(self, diff: str, current_readme: str) -> str:
        return await self.llm.update_readme(diff, current_readme)

    async def update_spec(self, commit_info: Dict[str, Any], diff: str, current_spec: str) -> str:
        return await self.llm.update_spec(commit_info, diff, current_spec)


class JulesReviewProvider(ReviewProvider):
    """Review provider using Jules / Google Code Review API with fallback to LLM."""

    def __init__(self, config: Config, fallback_provider: ReviewProvider):
        self.config = config
        self.fallback = fallback_provider
        self.api_key = config.JULES_API_KEY
        self.api_url = config.JULES_API_URL

    async def review_code(self, diff: str) -> Union[str, Dict[str, Any]]:
        """Review code using Jules API, with controlled fallback strategy.
        
        Returns structured error dict on 404 (misconfiguration) without fallback.
        Falls back to LLM only on transient errors (5xx, timeouts).
        
        Returns:
            str: Review content on success
            Dict[str, Any]: Error dict with success=False, error_type, message on 404
        """
        try:
            logger.info("Requesting code review from Jules API...")
            async with aiohttp.ClientSession() as session:
                payload = {
                    "diff": diff,
                    "context": "github_pr"
                }
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                async with session.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        review = data.get("review", "")
                        if review:
                            logger.info("Successfully received review from Jules")
                            return self._format_jules_review(review)
                    
                    # Handle 404 errors without fallback (likely misconfiguration)
                    if response.status == 404:
                        error_text = await response.text()
                        error_msg = "Jules API returned 404. Check JULES_SOURCE_ID/JULES_PROJECT_ID configuration."
                        logger.error(f"Code review skipped: {error_msg}")
                        logger.debug(f"Jules 404 response body: {error_text[:200] if error_text else 'No response body'}")
                        # Return error dict instead of falling back
                        return {
                            "success": False,
                            "error_type": "jules_404",
                            "message": error_msg,
                            "status_code": 404
                        }
                    
                    # For server errors (5xx), fall back to LLM
                    error_text = await response.text()
                    if response.status >= 500:
                        logger.warning(f"Jules API server error ({response.status}), falling back to LLM provider.")
                        return await self.fallback.review_code(diff)
                    
                    # For other client errors (4xx except 404), log and fall back
                    logger.warning(f"Jules API failed with status {response.status}: {error_text[:200] if error_text else 'No response body'}")
                    raise Exception(f"Jules API error: {response.status}")

        except aiohttp.ClientError as e:
            # Network/timeout errors - fall back to LLM
            logger.warning(f"Jules API network error: {e}. Falling back to LLM provider.")
            return await self.fallback.review_code(diff)
        except Exception as e:
            # Other errors - fall back to LLM
            logger.warning(f"Jules review failed: {e}. Falling back to LLM provider.")
            return await self.fallback.review_code(diff)

    async def update_readme(self, diff: str, current_readme: str) -> str:
        """Jules does not support README updates yet, using fallback."""
        logger.info("Jules does not support README updates, using fallback.")
        return await self.fallback.update_readme(diff, current_readme)

    async def update_spec(self, commit_info: Dict[str, Any], diff: str, current_spec: str) -> str:
        """Jules does not support Spec updates yet, using fallback."""
        logger.info("Jules does not support Spec updates, using fallback.")
        return await self.fallback.update_spec(commit_info, diff, current_spec)

    def _format_jules_review(self, raw_review: str) -> str:
        """Format Jules output to match our expected markdown structure."""
        # Assuming Jules returns raw markdown or text that needs wrapping
        # This can be adjusted based on actual Jules API response format
        return f"""# 🤖 Jules Code Review

{raw_review}

---
*Generated by Jules / Google Code Review API*
"""
