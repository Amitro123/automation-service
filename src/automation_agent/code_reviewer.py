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

    async def review_commit(self, commit_sha: str, post_as_issue: bool = False, pr_number: int = None, run_id: str = None) -> Dict[str, Any]:
        """Review a commit and post findings.

        Args:
            commit_sha: Commit SHA to review
            post_as_issue: If True, post as issue; otherwise as commit comment
            pr_number: If provided, post as PR review instead of commit comment
            run_id: Run ID for logging context

        Returns:
            Dictionary with success status, review content, and error details
        """
        log_prefix = f"[CODE_REVIEW] [run_id={run_id or 'N/A'}] [pr={pr_number or 'N/A'}]"
        logger.info(f"{log_prefix} Starting code review for commit {commit_sha[:7]}")

        try:
            # Fetch commit diff
            logger.info(f"{log_prefix} Fetching commit diff...")
            diff = await self.github.get_commit_diff(commit_sha)
            if not diff:
                error_msg = "Failed to fetch commit diff from GitHub"
                logger.error(f"{log_prefix} ❌ {error_msg}")
                return {
                    "success": False,
                    "review": None,
                    "error_type": "github_api_error",
                    "message": error_msg,
                    "usage_metadata": {},
                }
            logger.info(f"{log_prefix} ✅ Fetched diff ({len(diff)} chars)")

            # Fetch commit info for context
            logger.info(f"{log_prefix} Fetching commit info...")
            commit_info = await self.github.get_commit_info(commit_sha)
            if not commit_info:
                error_msg = "Failed to fetch commit info from GitHub"
                logger.error(f"{log_prefix} ❌ {error_msg}")
                return {
                    "success": False,
                    "review": None,
                    "error_type": "github_api_error",
                    "message": error_msg,
                    "usage_metadata": {},
                }
            logger.info(f"{log_prefix} ✅ Fetched commit info")

            # Generate code review with usage metadata
            logger.info(f"{log_prefix} Generating code review via provider...")
            try:
                review_result, usage_metadata = await self.provider.review_code(diff)
                logger.info(f"{log_prefix} Provider returned result (type: {type(review_result).__name__})")
                
                # Check if provider returned a structured error (e.g., Jules 404)
                if isinstance(review_result, dict) and not review_result.get("success", True):
                    error_type = review_result.get("error_type", "provider_error")
                    error_msg = review_result.get("message", "Unknown provider error")
                    logger.error(f"{log_prefix} ❌ Provider returned structured error: error_type={error_type}, message={error_msg}")
                    # Return error information without posting to GitHub
                    return {
                        "success": False,
                        "review": None,
                        "error_type": error_type,
                        "message": error_msg,
                        "usage_metadata": usage_metadata,
                    }
                
                if not review_result:
                    error_msg = "Provider returned empty review result"
                    logger.error(f"{log_prefix} ❌ {error_msg}")
                    return {
                        "success": False,
                        "review": None,
                        "error_type": "llm_error",
                        "message": error_msg,
                        "usage_metadata": usage_metadata,
                    }
                
                logger.info(f"{log_prefix} ✅ Review generated successfully ({len(str(review_result))} chars)")
                
            except Exception as e:
                error_msg = f"Review generation failed: {repr(e)}"
                logger.error(f"{log_prefix} ❌ {error_msg}", exc_info=True)
                return {
                    "success": False,
                    "review": None,
                    "error_type": "llm_error",
                    "message": error_msg,
                    "usage_metadata": {},
                }

            # Format the review
            logger.info(f"{log_prefix} Formatting review...")
            formatted_review = self._format_review(review_result)
            logger.info(f"{log_prefix} ✅ Review formatted ({len(formatted_review)} chars)")

            # Post review to GitHub
            post_success = False
            try:
                if pr_number:
                    # Post as PR review
                    logger.info(f"{log_prefix} Posting review on PR #{pr_number}...")
                    post_success = await self.github.post_pull_request_review(pr_number, formatted_review)
                    if post_success:
                        logger.info(f"{log_prefix} ✅ Successfully posted review on PR #{pr_number}")
                    else:
                        error_msg = f"GitHub API returned False when posting review on PR #{pr_number}"
                        logger.error(f"{log_prefix} ❌ {error_msg}")
                        return {
                            "success": False,
                            "review": formatted_review,
                            "error_type": "post_review_failed",
                            "message": error_msg,
                            "usage_metadata": usage_metadata,
                        }
                elif post_as_issue:
                    # Post as issue
                    title = f"🤖 Code Review: {commit_sha[:7]}"
                    logger.info(f"{log_prefix} Creating issue: {title}...")
                    issue_number = await self.github.create_issue(
                        title=title,
                        body=formatted_review,
                        labels=["automated-review", "code-quality"]
                    )
                    post_success = issue_number is not None
                    if post_success:
                        logger.info(f"{log_prefix} ✅ Created issue #{issue_number}")
                    else:
                        error_msg = "Failed to create GitHub issue"
                        logger.error(f"{log_prefix} ❌ {error_msg}")
                        return {
                            "success": False,
                            "review": formatted_review,
                            "error_type": "post_review_failed",
                            "message": error_msg,
                            "usage_metadata": usage_metadata,
                        }
                else:
                    # Post as commit comment
                    logger.info(f"{log_prefix} Posting commit comment on {commit_sha[:7]}...")
                    post_success = await self.github.post_commit_comment(commit_sha, formatted_review)
                    if post_success:
                        logger.info(f"{log_prefix} ✅ Posted commit comment on {commit_sha[:7]}")
                    else:
                        error_msg = f"Failed to post commit comment on {commit_sha[:7]}"
                        logger.error(f"{log_prefix} ❌ {error_msg}")
                        return {
                            "success": False,
                            "review": formatted_review,
                            "error_type": "post_review_failed",
                            "message": error_msg,
                            "usage_metadata": usage_metadata,
                        }
            except Exception as e:
                error_msg = f"Exception while posting review: {repr(e)}"
                logger.error(f"{log_prefix} ❌ {error_msg}", exc_info=True)
                return {
                    "success": False,
                    "review": formatted_review,
                    "error_type": "post_review_failed",
                    "message": error_msg,
                    "usage_metadata": usage_metadata,
                }
            
            # Log usage metadata
            if usage_metadata.get("total_tokens"):
                logger.info(f"{log_prefix} Used {usage_metadata['total_tokens']} tokens "
                           f"(cost: ${usage_metadata.get('estimated_cost', 0):.6f})")
            
            logger.info(f"{log_prefix} ✅ Code review completed successfully")
            return {
                "success": True,
                "review": formatted_review,
                "usage_metadata": usage_metadata,
            }
            
        except Exception as e:
            # Catch-all for any unexpected errors
            error_msg = f"Unexpected error in code review: {repr(e)}"
            logger.error(f"{log_prefix} ❌ {error_msg}", exc_info=True)
            return {
                "success": False,
                "review": None,
                "error_type": "unknown_error",
                "message": error_msg,
                "usage_metadata": {},
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