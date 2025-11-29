"""Automated code review module using LLM analysis."""

import logging
import json
from typing import Optional, Dict, Any
from .llm_client import LLMClient
from .github_client import GitHubClient
from .utils import clean_markdown_code_block

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

    async def review_commit(self, commit_sha: str, post_as_issue: bool = False) -> bool:
        """Review a commit and post findings.

        Args:
            commit_sha: Commit SHA to review
            post_as_issue: If True, post as issue; otherwise as commit comment

        Returns:
            True if review was posted successfully
        """
        logger.info(f"Starting code review for commit {commit_sha}")

        # Fetch commit diff
        diff = self.github.get_commit_diff(commit_sha)
        if not diff:
            logger.error("Failed to fetch commit diff")
            return False

        # Fetch commit info for context
        commit_info = self.github.get_commit_info(commit_sha)
        if not commit_info:
            logger.error("Failed to fetch commit info")
            return False

        # Generate code review
        try:
            review_json = await self.llm.analyze_code(diff)
            if not review_json:
                logger.error("Failed to generate code review")
                return False
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return False

        # Post review
        formatted_review = self._format_review(review_json)

        if post_as_issue:
            title = f"🤖 Code Review: {commit_sha[:7]}"
            issue_number = self.github.create_issue(
                title=title,
                body=formatted_review,
                labels=["automated-review", "code-quality"]
            )
            return issue_number is not None
        else:
            return self.github.post_commit_comment(commit_sha, formatted_review)

    def _format_review(self, review_json_str: str) -> str:
        """Format the LLM analysis JSON into a GitHub-friendly review.

        Args:
            review_json_str: Raw LLM analysis JSON string

        Returns:
            Formatted review with header and footer
        """
        try:
            cleaned_json = clean_markdown_code_block(review_json_str)
            review_data = json.loads(cleaned_json)
        except json.JSONDecodeError:
            logger.error("Failed to parse review JSON, using raw output")
            return f"# 🤖 Automated Code Review\n\nError parsing JSON output. Raw output:\n\n{review_json_str}"

        header = """# 🤖 Automated Code Review

*This review was generated automatically by the GitHub Automation Agent.*

---

"""
        content = ""

        # Strengths
        if review_data.get("strengths"):
            content += "## ✅ Strengths\n"
            for strength in review_data["strengths"]:
                content += f"- {strength}\n"
            content += "\n"

        # Issues
        if review_data.get("issues"):
            content += "## ⚠️ Issues\n"
            for issue in review_data["issues"]:
                content += f"- **{issue.get('severity', 'unknown').upper()}**: `{issue.get('file', 'unknown')}:{issue.get('line', '?')}` - {issue.get('message', '')}\n"
            content += "\n"

        # Suggestions
        if review_data.get("suggestions"):
            content += "## 💡 Suggestions\n"
            for suggestion in review_data["suggestions"]:
                content += f"- {suggestion}\n"
            content += "\n"

        footer = """\n---

*💡 This is an automated review. Please use your judgment and discuss with your team before making changes.*
"""
        return header + content + footer
