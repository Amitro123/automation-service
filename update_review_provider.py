"""Script to safely update review_provider.py with Jules 404 handling."""

# Read the original file
with open("src/automation_agent/review_provider.py", "r", encoding="utf-8") as f:
    content = f.read()

# Update the review_code method in JulesReviewProvider
old_method = '''    async def review_code(self, diff: str) -> str:
        """Review code using Jules API, falling back to LLM on failure."""
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
                    
                    error_text = await response.text()
                    logger.warning(f"Jules API failed with status {response.status}: {error_text[:200] if error_text else 'No response body'}")
                    raise Exception(f"Jules API error: {response.status}")

        except Exception as e:
            logger.warning(f"Jules review failed: {e}. Falling back to LLM provider.")
            return await self.fallback.review_code(diff)'''

new_method = '''    async def review_code(self, diff: str):
        """Review code using Jules API, with controlled fallback strategy.
        
        Returns structured error dict on 404 (misconfiguration) without fallback.
        Falls back to LLM only on transient errors (5xx, timeouts).
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
                        error_msg = f"Jules API returned 404. Check JULES_SOURCE_ID/JULES_PROJECT_ID configuration."
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
            return await self.fallback.review_code(diff)'''

content = content.replace(old_method, new_method)

# Write the updated content
with open("src/automation_agent/review_provider.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✓ Successfully updated review_provider.py with Jules 404 handling")
