import asyncio
import logging
from typing import Dict, Any, List, Callable, Optional
from .github_client import GitHubClient
from .code_reviewer import CodeReviewer
from .readme_updater import ReadmeUpdater
from .spec_updater import SpecUpdater
from .config import Config

logger = logging.getLogger(__name__)


class AutomationOrchestrator:
    """Orchestrates code review, README updates, and spec documentation."""

    def __init__(
        self,
        github_client: GitHubClient,
        code_reviewer: CodeReviewer,
        readme_updater: ReadmeUpdater,
        spec_updater: SpecUpdater,
        config: Config,
    ):
        """Initialize orchestrator.

        Args:
            github_client: GitHub API client
            code_reviewer: Code review module
            readme_updater: README update module
            spec_updater: Spec update module
            config: Application configuration
        """
        self.github = github_client
        self.code_reviewer = code_reviewer
        self.readme_updater = readme_updater
        self.spec_updater = spec_updater
        self.config = config

    async def run_automation(self, event_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process a push event and execute all automation tasks in parallel.

        Args:
            event_payload: GitHub webhook payload

        Returns:
            Dictionary with results of all tasks
        """
        diff_info = self._extract_diff_info(event_payload)
        if not diff_info:
            return {"success": False, "error": "Invalid payload or no commits"}

        commit_sha = diff_info["commit_sha"]
        branch = diff_info["branch"]
        logger.info(f"Starting automation orchestration for commit {commit_sha[:7]}")

        # Define tasks to run in parallel
        tasks = [
            self._run_code_review(commit_sha),
            self._run_readme_update(commit_sha, branch),
            self._run_spec_update(commit_sha, branch),
        ]

        # Execute tasks
        task_results = await self._run_parallel_tasks(tasks)

        results = {
            "success": all(r.get("success", False) for r in task_results),
            "commit_sha": commit_sha,
            "branch": branch,
            "tasks": {
                "code_review": task_results[0],
                "readme_update": task_results[1],
                "spec_update": task_results[2],
            },
        }

        logger.info(f"Automation orchestration completed. Success: {results['success']}")
        return results

    def _extract_diff_info(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract relevant information from the webhook payload.

        Args:
            payload: Webhook payload

        Returns:
            Dictionary with commit_sha, branch, and message, or None if invalid
        """
        try:
            head_commit = payload.get("head_commit")
            if not head_commit:
                return None

            ref = payload.get("ref", "")
            if ref.startswith("refs/heads/"):
                branch = ref.replace("refs/heads/", "", 1)
            else:
                branch = ref

            return {
                "commit_sha": head_commit.get("id"),
                "branch": branch,
                "message": head_commit.get("message", ""),
            }
        except Exception as e:
            logger.error(f"Failed to extract diff info: {e}")
            return None

    async def _run_parallel_tasks(self, tasks: List[Callable]) -> List[Dict[str, Any]]:
        """Run multiple tasks in parallel using asyncio.gather.

        Args:
            tasks: List of coroutines to execute

        Returns:
            List of results from each task
        """
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_code_review(self, commit_sha: str) -> Dict[str, Any]:
        """Run code review task."""
        try:
            logger.info("Task 1: Running code review...")
            # Call async method directly
            review_success = await self.code_reviewer.review_commit(
                commit_sha=commit_sha,
                post_as_issue=self.config.POST_REVIEW_AS_ISSUE,
            )
            return {
                "success": review_success,
                "status": "completed" if review_success else "failed",
                "posted_as_issue": self.config.POST_REVIEW_AS_ISSUE,
            }
        except Exception as e:
            logger.error(f"Code review failed: {e}", exc_info=True)
            return {"success": False, "status": "error", "error": str(e)}

    async def _run_readme_update(self, commit_sha: str, branch: str) -> Dict[str, Any]:
        """Run README update task."""
        try:
            logger.info("Task 2: Checking README updates...")
            # Call async method directly
            updated_readme = await self.readme_updater.update_readme(
                commit_sha=commit_sha, branch=branch
            )

            if updated_readme:
                if self.config.CREATE_PR:
                    pr_result = await asyncio.to_thread(
                        self._create_documentation_pr,
                        branch=branch,
                        readme_content=updated_readme,
                        commit_sha=commit_sha,
                    )
                    return {
                        "success": pr_result["success"],
                        "status": "completed",
                        "pr_created": pr_result["success"],
                        "pr_number": pr_result.get("pr_number"),
                    }
                elif self.config.AUTO_COMMIT:
                    commit_success = await asyncio.to_thread(
                        self.github.update_file,
                        file_path="README.md",
                        content=updated_readme,
                        message=f"docs: Auto-update README.md from {commit_sha[:7]}",
                        branch=branch,
                    )
                    return {
                        "success": commit_success,
                        "status": "completed" if commit_success else "failed",
                        "auto_committed": commit_success,
                    }
                else:
                    return {
                        "success": True,
                        "status": "completed",
                        "note": "Updates generated but not committed",
                    }
            else:
                return {
                    "success": True,
                    "status": "skipped",
                    "reason": "No updates needed",
                }
        except Exception as e:
            logger.error(f"README update failed: {e}", exc_info=True)
            return {"success": False, "status": "error", "error": str(e)}

    async def _run_spec_update(self, commit_sha: str, branch: str) -> Dict[str, Any]:
        """Run spec.md update task."""
        try:
            logger.info("Task 3: Updating spec.md...")
            # Call async method directly
            updated_spec = await self.spec_updater.update_spec(
                commit_sha=commit_sha, branch=branch
            )

            if updated_spec:
                if self.config.CREATE_PR:
                    # Note: In parallel execution, we can't easily append to the README PR
                    # because we don't know if it exists yet.
                    # For simplicity in this async version, we'll create a separate PR or
                    # try to find an existing one (omitted for brevity, creating new one).
                    pr_result = await asyncio.to_thread(
                        self._create_documentation_pr,
                        branch=branch,
                        spec_content=updated_spec,
                        commit_sha=commit_sha,
                    )
                    return {
                        "success": pr_result["success"],
                        "status": "completed",
                        "pr_created": pr_result["success"],
                        "pr_number": pr_result.get("pr_number"),
                    }
                elif self.config.AUTO_COMMIT:
                    commit_success = await asyncio.to_thread(
                        self.github.update_file,
                        file_path="spec.md",
                        content=updated_spec,
                        message=f"docs: Auto-update spec.md from {commit_sha[:7]}",
                        branch=branch,
                    )
                    return {
                        "success": commit_success,
                        "status": "completed" if commit_success else "failed",
                        "auto_committed": commit_success,
                    }
                else:
                    return {
                        "success": True,
                        "status": "completed",
                        "note": "Updates generated but not committed",
                    }
            else:
                return {
                    "success": False,
                    "status": "failed",
                    "reason": "Failed to generate spec update",
                }
        except Exception as e:
            logger.error(f"Spec update failed: {e}", exc_info=True)
            return {"success": False, "status": "error", "error": str(e)}

    def _create_documentation_pr(
        self,
        branch: str,
        readme_content: str = None,
        spec_content: str = None,
        commit_sha: str = "",
    ) -> Dict[str, Any]:
        """Create a pull request with documentation updates.

        Args:
            branch: Base branch
            readme_content: Updated README content (optional)
            spec_content: Updated spec content (optional)
            commit_sha: Commit SHA that triggered the update

        Returns:
            Dictionary with PR creation result
        """
        # Use a unique branch name for each type of update to avoid conflicts in parallel
        suffix = "readme" if readme_content else "spec"
        pr_branch = f"automation/docs-{suffix}-{commit_sha[:7]}"

        try:
            # Create branch
            if not self.github.create_branch(pr_branch, from_branch=branch):
                return {"success": False, "error": "Failed to create branch"}

            # Commit files
            if readme_content:
                if not self.github.update_file(
                    file_path="README.md",
                    content=readme_content,
                    message=f"docs: Auto-update README.md from {commit_sha[:7]}",
                    branch=pr_branch,
                ):
                    return {"success": False, "error": "Failed to update README.md"}

            if spec_content:
                if not self.github.update_file(
                    file_path="spec.md",
                    content=spec_content,
                    message=f"docs: Auto-update spec.md from {commit_sha[:7]}",
                    branch=pr_branch,
                ):
                    return {"success": False, "error": "Failed to update spec.md"}

            # Create PR
            pr_title = f"🤖 Auto-update {suffix} from {commit_sha[:7]}"
            pr_body = f"""## Automated Documentation Update

This PR contains automated documentation updates generated from commit `{commit_sha[:7]}`.

### Changes Included:
{"- ✅ README.md updated" if readme_content else ""}
{"- ✅ spec.md updated" if spec_content else ""}

### Review Instructions:
1. Review the documentation changes for accuracy
2. Ensure all new features/changes are properly documented
3. Check for any formatting issues
4. Merge if everything looks good

---
*This PR was created automatically by the GitHub Automation Agent.*
"""

            pr_number = self.github.create_pull_request(
                title=pr_title, body=pr_body, head=pr_branch, base=branch
            )

            if pr_number:
                logger.info(f"Created documentation PR #{pr_number}")
                return {"success": True, "pr_number": pr_number, "branch": pr_branch}
            else:
                return {"success": False, "error": "Failed to create PR"}

        except Exception as e:
            logger.error(f"Failed to create documentation PR: {e}")
            return {"success": False, "error": str(e)}