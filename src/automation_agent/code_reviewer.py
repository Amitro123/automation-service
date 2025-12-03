"""Automated code review module using review provider abstraction."""

import logging
from typing import Optional, Dict, Any
from .review_provider import ReviewProvider
from .github_client import GitHubClient

logger = logging.getLogger(__name__)


class CodeReviewer:
    """Automated code review with quality, security, and best practices analysis."""

    def __init__(self, github_client: GitHubClient, review_provider: ReviewProvider):
        """Initialize code reviewer.

        Args:
            github_client: GitHub API client
            review_provider: Provider for code review analysis
        """
        self.github = github_client
        self.provider = review_provider

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

        # Generate code review with usage metadata
        try:
            review_result, usage_metadata = await self.provider.review_code(diff)
            
            # Check if provider returned a structured error (e.g., Jules 404)
            if isinstance(review_result, dict) and not review_result.get("success", True):
                error_type = review_result.get("error_type", "unknown")
                error_msg = review_result.get("message", "Unknown error")
                logger.error(f"Review provider error ({error_type}): {error_msg}")
                # Return error information without posting to GitHub, but include metadata
                return {
                    "success": False,
                    "review": None,
                    "error_type": error_type,
                    "message": error_msg,
                    "usage_metadata": usage_metadata,
                }
            
            if not review_result:
                logger.error("Failed to generate code review")
                return {"success": False, "review": None, "usage_metadata": usage_metadata}
        except Exception as e:
            logger.error(f"Review analysis failed: {e}")
            return {"success": False, "review": None, "usage_metadata": {}}

        formatted_review = self._format_review(review_result)

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
        
        # Log usage metadata
        if usage_metadata.get("total_tokens"):
            logger.info(f"Code review used {usage_metadata['total_tokens']} tokens "
                       f"(cost: ${usage_metadata.get('estimated_cost', 0):.6f})")
            
        return {
            "success": success,
            "review": formatted_review,
            "usage_metadata": usage_metadata,
        }

    def _format_review(self, analysis: str) -> str:
        """Format the analysis into a GitHub-friendly review.

        Args:
            analysis: Raw analysis text

        Returns:
            Formatted review with header and footer
        """
        # If the analysis already contains the header (e.g. from JulesReviewProvider), don't add it again
        if "# 🤖" in analysis:
            return analysis

        header = """# 🤖 Automated Code Review

*This review was generated automatically by the GitHub Automation Agent.*

---

"""
        footer = """\n\n---

*💡 This is an automated review. Please use your judgment and discuss with your team before making changes.*
"""
        return header + analysis + footer