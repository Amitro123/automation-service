"""Automated README.md update module."""

import logging
import re
from typing import Optional, Dict, List, Union, Any
from .review_provider import ReviewProvider
from .llm_client import RateLimitError
from .github_client import GitHubClient

logger = logging.getLogger(__name__)


class ReadmeUpdater:
    """Automated README.md updates based on code changes."""

    def __init__(self, github_client: GitHubClient, review_provider: ReviewProvider):
        """Initialize README updater.

        Args:
            github_client: GitHub API client
            review_provider: Provider for analysis and updates
        """
        self.github = github_client
        self.provider = review_provider

    async def update_readme(self, commit_sha: str, branch: str = "main") -> Optional[Union[str, Dict[str, Any]]]:
        """Update README.md based on code changes.

        Args:
            commit_sha: Commit SHA to analyze
            branch: Branch to update README on

        Returns:
            str: Updated README content on success
            Dict[str, Any]: Error dict with success=False, error_type, message on rate limit
            None: If no updates needed
        """
        logger.info(f"Analyzing commit {commit_sha} for README updates")

        # Fetch commit diff and info
        diff = await self.github.get_commit_diff(commit_sha)
        if not diff:
            logger.error("Failed to fetch commit diff")
            return None

        commit_info = await self.github.get_commit_info(commit_sha)
        if not commit_info:
            logger.error("Failed to fetch commit info")
            return None

        # Fetch current README
        current_readme = await self.github.get_file_content("README.md", ref=branch)
        if current_readme is None:
            logger.warning("README.md not found, will create new one")
            current_readme = "# Project\n\nProject description.\n"

        # Generate updated README
        try:
            updated_readme = await self.provider.update_readme(diff, current_readme)
            updated_readme = self._clean_readme_output(updated_readme)
        except RateLimitError as e:
            logger.exception("README update failed: LLM rate-limited (429)")
            return {
                "success": False,
                "error_type": "llm_rate_limited",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Failed to generate README updates: {e}")
            return None

        if not updated_readme or updated_readme == current_readme:
            logger.info("No README updates needed")
            return None

        logger.info("README updates generated")
        return updated_readme

    def _clean_readme_output(self, readme: str) -> str:
        """Clean up LLM output to extract pure README content.

        Args:
            readme: Raw LLM output

        Returns:
            Cleaned README content
        """
        # Remove markdown code block wrappers if present
        readme = re.sub(r'^```markdown\s*\n', '', readme, flags=re.MULTILINE)
        readme = re.sub(r'^```\s*\n', '', readme, flags=re.MULTILINE)
        readme = re.sub(r'\n```\s*$', '', readme, flags=re.MULTILINE)
        
        # Remove any leading/trailing whitespace
        readme = readme.strip()
        
        return readme