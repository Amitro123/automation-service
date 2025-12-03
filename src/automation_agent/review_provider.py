"""Review provider abstraction for pluggable code review engines."""

import logging
import aiohttp
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from .llm_client import LLMClient
from .config import Config

logger = logging.getLogger(__name__)


class ReviewProvider(ABC):
    """Abstract base class for code review providers."""

    @abstractmethod
    async def review_code(self, diff: str) -> tuple[Union[str, Dict[str, Any]], Dict[str, Any]]:
        """Analyze code changes and provide a review.
        
        Returns:
            Tuple of (review_content_or_error_dict, usage_metadata)
        """
        pass

    @abstractmethod
    async def update_readme(self, diff: str, current_readme: str) -> tuple[str, Dict[str, Any]]:
        """Generate updates for README.md.
        
        Returns:
            Tuple of (updated_readme, usage_metadata)
        """
        pass

    @abstractmethod
    async def update_spec(self, commit_info: Dict[str, Any], diff: str, current_spec: str) -> tuple[str, Dict[str, Any]]:
        """Update spec.md based on commit info.
        
        Returns:
            Tuple of (updated_spec, usage_metadata)
        """
        pass


class LLMReviewProvider(ReviewProvider):
    """Review provider using the existing LLMClient (Gemini/OpenAI/Anthropic)."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def review_code(self, diff: str) -> tuple[Union[str, Dict[str, Any]], Dict[str, Any]]:
        """Review code using LLM.
        
        Returns:
            Tuple of (review_content_or_error_dict, usage_metadata)
        """
        try:
            review, metadata = await self.llm.analyze_code(diff)
            return review, metadata
        except Exception as e:
            # LLMClient already raises RateLimitError for 429s
            # This catches any other unexpected errors
            logger.error(f"LLM review failed: {e}")
            error_dict = {
                "success": False,
                "error_type": "llm_error",
                "message": str(e)
            }
            return error_dict, {}

    async def update_readme(self, diff: str, current_readme: str) -> tuple[str, Dict[str, Any]]:
        return await self.llm.update_readme(diff, current_readme)

    async def update_spec(self, commit_info: Dict[str, Any], diff: str, current_spec: str) -> tuple[str, Dict[str, Any]]:
        return await self.llm.update_spec(commit_info, diff, current_spec)


class JulesReviewProvider(ReviewProvider):
    """Review provider using Jules API (https://developers.google.com/jules/api) with fallback to LLM."""

    def __init__(self, config: Config, fallback_provider: ReviewProvider):
        self.config = config
        self.fallback = fallback_provider
        self.api_key = config.JULES_API_KEY
        self.base_url = config.JULES_API_URL  # https://jules.googleapis.com/v1alpha
        self.source_id = config.JULES_SOURCE_ID  # e.g., "sources/github/owner/repo"
        self.project_id = config.JULES_PROJECT_ID  # Optional

    async def review_code(self, diff: str) -> tuple[Union[str, Dict[str, Any]], Dict[str, Any]]:
        """Review code using Jules API by creating a session.
        
        Jules API workflow:
        1. Create a session with the diff/prompt
        2. Wait for Jules to process (session becomes active)
        3. Extract the review from session outputs
        
        Returns structured error dict on 404 (misconfiguration) without fallback.
        Falls back to LLM only on transient errors (5xx, timeouts).
        
        Returns:
            Tuple of (review_content_or_error_dict, usage_metadata)
        """
        try:
            logger.info("[JULES] Requesting code review from Jules API...")
            logger.info(f"[JULES] Source: {self.source_id}")
            
            async with aiohttp.ClientSession() as session:
                # Step 1: Create a Jules session for code review
                create_url = f"{self.base_url}/sessions"
                payload = {
                    "prompt": f"Please review this code change:\n\n```diff\n{diff[:5000]}\n```",  # Limit diff size
                    "sourceContext": {
                        "source": self.source_id,
                    },
                    "title": "Code Review Request",
                    "requirePlanApproval": False,  # Auto-approve for automated reviews
                }
                
                # Add project_id if configured
                if self.project_id:
                    payload["projectId"] = self.project_id
                
                headers = {
                    "X-Goog-Api-Key": self.api_key,  # Jules uses X-Goog-Api-Key, not Bearer
                    "Content-Type": "application/json"
                }
                
                logger.info(f"[JULES] Creating session at {create_url}")
                logger.debug(f"[JULES] Request payload: {payload}")
                
                async with session.post(
                    create_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    response_text = await response.text()
                    logger.info(f"[JULES] Response status: {response.status}")
                    
                    # Handle 404 errors without fallback (likely misconfiguration)
                    if response.status == 404:
                        error_msg = f"Jules API returned 404. Check JULES_SOURCE_ID configuration. Source: {self.source_id}"
                        logger.error(f"[JULES] ❌ {error_msg}")
                        logger.debug(f"[JULES] 404 response body: {response_text[:500]}")
                        error_dict = {
                            "success": False,
                            "error_type": "jules_404",
                            "message": error_msg,
                            "status_code": 404
                        }
                        return error_dict, {}
                    
                    # Handle 401/403 authentication errors
                    if response.status in (401, 403):
                        error_msg = f"Jules API authentication failed ({response.status}). Check JULES_API_KEY."
                        logger.error(f"[JULES] ❌ {error_msg}")
                        logger.debug(f"[JULES] Auth error response: {response_text[:500]}")
                        error_dict = {
                            "success": False,
                            "error_type": "jules_auth_error",
                            "message": error_msg,
                            "status_code": response.status
                        }
                        return error_dict, {}
                    
                    # Handle other 4xx errors
                    if 400 <= response.status < 500:
                        error_msg = f"Jules API client error ({response.status}): {response_text[:200]}"
                        logger.error(f"[JULES] ❌ {error_msg}")
                        error_dict = {
                            "success": False,
                            "error_type": "jules_client_error",
                            "message": error_msg,
                            "status_code": response.status
                        }
                        return error_dict, {}
                    
                    # Handle server errors (5xx) - fall back to LLM
                    if response.status >= 500:
                        logger.warning(f"[JULES] Jules API server error ({response.status}), falling back to LLM provider.")
                        logger.debug(f"[JULES] Server error response: {response_text[:500]}")
                        return await self.fallback.review_code(diff)
                    
                    # Success - parse session response
                    if response.status == 200:
                        try:
                            data = await response.json()
                            session_id = data.get("id") or data.get("name", "").split("/")[-1]
                            logger.info(f"[JULES] ✅ Session created: {session_id}")
                            
                            # Step 2: Poll session for completion (Jules processes async)
                            review_text = await self._wait_for_session_completion(session, session_id, headers)
                            
                            if review_text:
                                logger.info(f"[JULES] ✅ Review received ({len(review_text)} chars)")
                                metadata = {"provider": "jules", "model": "jules-api", "session_id": session_id}
                                return self._format_jules_review(review_text), metadata
                            else:
                                logger.warning("[JULES] Session completed but no review content found")
                                error_dict = {
                                    "success": False,
                                    "error_type": "jules_empty_response",
                                    "message": "Jules session completed but returned no review content"
                                }
                                return error_dict, {}
                                
                        except Exception as e:
                            logger.error(f"[JULES] Failed to parse session response: {e}")
                            logger.debug(f"[JULES] Response text: {response_text[:500]}")
                            raise
                    
                    # Unexpected status code
                    error_msg = f"Unexpected Jules API response: {response.status}"
                    logger.error(f"[JULES] ❌ {error_msg}")
                    raise Exception(error_msg)

        except aiohttp.ClientError as e:
            # Network/timeout errors - fall back to LLM
            logger.warning(f"[JULES] Network error: {e}. Falling back to LLM provider.")
            return await self.fallback.review_code(diff)
        except Exception as e:
            # Other errors - fall back to LLM
            logger.warning(f"[JULES] Unexpected error: {e}. Falling back to LLM provider.")
            logger.exception("[JULES] Full traceback:")
            return await self.fallback.review_code(diff)
    
    async def _wait_for_session_completion(self, session: aiohttp.ClientSession, session_id: str, headers: Dict[str, str], max_polls: int = 10, poll_interval: int = 3) -> Optional[str]:
        """Poll Jules session until it completes and extract review content.
        
        Args:
            session: aiohttp session
            session_id: Jules session ID
            headers: Request headers with API key
            max_polls: Maximum number of polling attempts
            poll_interval: Seconds between polls
            
        Returns:
            Review text or None if not found
        """
        import asyncio
        
        get_url = f"{self.base_url}/sessions/{session_id}"
        logger.info(f"[JULES] Polling session status: {session_id}")
        
        for attempt in range(max_polls):
            await asyncio.sleep(poll_interval if attempt > 0 else 0)
            
            try:
                async with session.get(get_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        state = data.get("state", "UNKNOWN")
                        logger.info(f"[JULES] Poll {attempt + 1}/{max_polls}: state={state}")
                        
                        # Check if session has outputs (PR, files, etc.)
                        outputs = data.get("outputs", [])
                        if outputs:
                            # Extract review content from outputs
                            # Jules may return PR descriptions, file changes, or text outputs
                            review_parts = []
                            for output in outputs:
                                if "pullRequest" in output:
                                    pr = output["pullRequest"]
                                    review_parts.append(f"## Pull Request\n{pr.get('description', '')}")
                                elif "text" in output:
                                    review_parts.append(output["text"])
                                elif "fileChanges" in output:
                                    changes = output["fileChanges"]
                                    review_parts.append(f"## File Changes\n{len(changes)} files modified")
                            
                            if review_parts:
                                return "\n\n".join(review_parts)
                        
                        # If state is terminal but no outputs, return state info
                        if state in ("COMPLETED", "FAILED", "CANCELLED"):
                            logger.warning(f"[JULES] Session {state} but no outputs found")
                            return f"Session {state}. No detailed review available."
                        
                    else:
                        logger.warning(f"[JULES] Poll failed with status {response.status}")
                        
            except Exception as e:
                logger.warning(f"[JULES] Poll attempt {attempt + 1} failed: {e}")
        
        logger.warning(f"[JULES] Session polling timed out after {max_polls} attempts")
        return None

    async def update_readme(self, diff: str, current_readme: str) -> tuple[str, Dict[str, Any]]:
        """Jules does not support README updates yet, using fallback."""
        logger.info("Jules does not support README updates, using fallback.")
        return await self.fallback.update_readme(diff, current_readme)

    async def update_spec(self, commit_info: Dict[str, Any], diff: str, current_spec: str) -> tuple[str, Dict[str, Any]]:
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
