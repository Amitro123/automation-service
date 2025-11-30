"""Automated code review module using LLM analysis."""

import logging
from typing import Optional, Dict, Any
from .llm_client import LLMClient
from .github_client import GitHubClient

logger = logging.getLogger(__name__)


class CodeReviewer:
    """Automated code review with quality, security, and best practices analysis."""

    def __init__(self, github_client: GitHubClient, llm_client: LLMClient):
        """Initialize code reviewer.

        Args:
            github_client: GitHub API client
            llm_client: LLM client for analysis
        """
        self.github = github_client
        self.llm = llm_client

    async def review_commit(self, commit_sha: str, post_as_issue: bool = False) -> Dict[str, Any]:
        """Review a commit and post findings.

        Args:
            commit_sha: Commit SHA to review
            post_as_issue: If True, post as issue; otherwise as commit comment

        Returns:
            Dictionary with success status and review content
        """
        logger.info(f"Starting code review for commit {commit_sha}")

        # Fetch commit diff
        diff = await self.github.get_commit_diff(commit_sha)
        if not diff:
            logger.error("Failed to fetch commit diff")
            return {"success": False, "review": None}

        # Fetch commit info for context
        commit_info = await self.github.get_commit_info(commit_sha)
        if not commit_info:
            logger.error("Failed to fetch commit info")
            return {"success": False, "review": None}

        # Generate code review
        try:
            review = await self.llm.analyze_code(diff)
            if not review:
                logger.error("Failed to generate code review")
                return {"success": False, "review": None}
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {"success": False, "review": None}

        formatted_review = self._format_review(review)

        # Post review
        success = False
        if post_as_issue:
            title = f"🤖 Code Review: {commit_sha[:7]}"
            issue_number = await self.github.create_issue(
                title=title,
                body=formatted_review,
                labels=["automated-review", "code-quality"]
            )
            success = issue_number is not None
        else:
            success = await self.github.post_commit_comment(commit_sha, formatted_review)
            
        return {"success": success, "review": formatted_review}

    def _format_review(self, analysis: str) -> str:
        """Format the LLM analysis into a GitHub-friendly review.

        Args:
            analysis: Raw LLM analysis text

        Returns:
            Formatted review with header and footer
        """
        header = """# 🤖 Automated Code Review

*This review was generated automatically by the GitHub Automation Agent.*

---

"""
        footer = """\n\n---

*💡 This is an automated review. Please use your judgment and discuss with your team before making changes.*
"""
        return header + analysis + footer