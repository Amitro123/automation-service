import asyncio
import logging
from typing import Dict, Any, List, Callable, Optional
from .github_client import GitHubClient
from .code_reviewer import CodeReviewer
from .readme_updater import ReadmeUpdater
from .spec_updater import SpecUpdater
from .code_review_updater import CodeReviewUpdater
from .config import Config
from .session_memory import SessionMemoryStore
from .trigger_filter import TriggerFilter, TriggerContext, TriggerType, RunType
from .llm_client import RateLimitError

logger = logging.getLogger(__name__)


class AutomationOrchestrator:
    """Orchestrates code review, README updates, and spec documentation."""

    def __init__(
        self,
        github_client: GitHubClient,
        code_reviewer: CodeReviewer,
        readme_updater: ReadmeUpdater,
        spec_updater: SpecUpdater,
        code_review_updater: CodeReviewUpdater,
        session_memory: SessionMemoryStore,
        config: Config,
    ):
        """Initialize orchestrator.

        Args:
            github_client: GitHub API client
            code_reviewer: Code review module
            readme_updater: README update module
            spec_updater: Spec update module
            code_review_updater: Code review log updater
            session_memory: Session memory store
            config: Application configuration
        """
        self.github = github_client
        self.code_reviewer = code_reviewer
        self.readme_updater = readme_updater
        self.spec_updater = spec_updater
        self.code_review_updater = code_review_updater
        self.session_memory = session_memory
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
        
        # Start session tracking
        run_id = f"run_{commit_sha[:7]}_{int(asyncio.get_event_loop().time())}"
        self.session_memory.add_run(run_id, commit_sha, branch)
        
        logger.info(f"Starting automation orchestration for commit {commit_sha[:7]} (Run ID: {run_id})")

        # Define tasks to run in parallel
        tasks = [
            self._run_code_review(commit_sha, branch, run_id),
            self._run_readme_update(commit_sha, branch, run_id),
            self._run_spec_update(commit_sha, branch, run_id),
        ]

        # Execute tasks
        task_results = await self._run_parallel_tasks(tasks)

        results = {
            "success": all(r.get("success", False) for r in task_results),
            "commit_sha": commit_sha,
            "branch": branch,
            "run_id": run_id,
            "tasks": {
                "code_review": task_results[0],
                "readme_update": task_results[1],
                "spec_update": task_results[2],
            },
        }

        # Update final status
        status = "completed" if results["success"] else "failed"
        summary = "All tasks completed successfully" if results["success"] else "Some tasks failed"
        self.session_memory.update_run_status(run_id, status, summary)

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

    async def _run_code_review(self, commit_sha: str, branch: str, run_id: str) -> Dict[str, Any]:
        """Run code review task."""
        try:
            logger.info("Task 1: Running code review...")
            # Call async method directly
            review_result = await self.code_reviewer.review_commit(
                commit_sha=commit_sha,
                post_as_issue=self.config.POST_REVIEW_AS_ISSUE,
            )
            
            review_success = review_result.get("success", False)
            review_content = review_result.get("review", "")
            
            # Check for structured error (Jules 404, etc.)
            if not review_success and review_result.get("error_type"):
                error_type = review_result.get("error_type")
                error_msg = review_result.get("message", "Unknown error")
                # Mark task as failed in session memory
                self.session_memory.mark_task_failed(run_id, "code_review", error_msg, error_type)
                # Return error without posting to GitHub or creating PRs
                result = {
                    "success": False,
                    "status": "failed",
                    "error_type": error_type,
                    "message": error_msg
                }
                self.session_memory.update_task_result(run_id, "code_review", result)
                return result
            
            log_updated = False
            if review_success and review_content:
                updated_log = await self.code_review_updater.update_review_log(
                    commit_sha=commit_sha,
                    review_content=review_content,
                    branch=branch
                )
                
                if updated_log:
                    if self.config.AUTO_COMMIT:
                        log_updated = await self.github.update_file(
                            file_path=CodeReviewUpdater.LOG_FILE,
                            content=updated_log,
                            message=f"docs: Update automated review log for {commit_sha[:7]}",
                            branch=branch
                        )
                    else:
                        log_updated = True # Generated but not committed

            result = {
                "success": review_success,
                "status": "completed" if review_success else "failed",
                "posted_as_issue": self.config.POST_REVIEW_AS_ISSUE,
                "log_updated": log_updated
            }
            self.session_memory.update_task_result(run_id, "code_review", result)
            return result
        except Exception as e:
            logger.error(f"Code review failed: {e}", exc_info=True)
            result = {"success": False, "status": "error", "error": str(e)}
            self.session_memory.update_task_result(run_id, "code_review", result)
            return result

    async def _run_readme_update(self, commit_sha: str, branch: str, run_id: str) -> Dict[str, Any]:
        """Run README update task."""
        try:
            logger.info("Task 2: Checking README updates...")
            # Call async method directly
            updated_readme = await self.readme_updater.update_readme(
                commit_sha=commit_sha, branch=branch
            )

            # Check if result is an error dict (rate limit, etc.)
            if isinstance(updated_readme, dict) and not updated_readme.get("success", True):
                error_type = updated_readme.get("error_type", "unknown")
                error_msg = updated_readme.get("message", "Unknown error")
                # Mark task as failed in session memory
                self.session_memory.mark_task_failed(run_id, "readme_update", error_msg, error_type)
                result = {
                    "success": False,
                    "status": "failed",
                    "error_type": error_type,
                    "message": error_msg
                }
                self.session_memory.update_task_result(run_id, "readme_update", result)
                return result

            if updated_readme:
                if self.config.CREATE_PR:
                    pr_result = await self._create_documentation_pr(
                        branch=branch,
                        readme_content=updated_readme,
                        commit_sha=commit_sha,
                    )
                    result = {
                        "success": pr_result["success"],
                        "status": "completed",
                        "pr_created": pr_result["success"],
                        "pr_number": pr_result.get("pr_number"),
                    }
                elif self.config.AUTO_COMMIT:
                    commit_success = await self.github.update_file(
                        file_path="README.md",
                        content=updated_readme,
                        message=f"docs: Auto-update README.md from {commit_sha[:7]}",
                        branch=branch,
                    )
                    result = {
                        "success": commit_success,
                        "status": "completed" if commit_success else "failed",
                        "auto_committed": commit_success,
                    }
                else:
                    result = {
                        "success": True,
                        "status": "completed",
                        "note": "Updates generated but not committed",
                    }
            else:
                result = {
                    "success": True,
                    "status": "skipped",
                    "reason": "No updates needed",
                }
            
            self.session_memory.update_task_result(run_id, "readme_update", result)
            return result
        except Exception as e:
            logger.error(f"README update failed: {e}", exc_info=True)
            result = {"success": False, "status": "error", "error": str(e)}
            self.session_memory.update_task_result(run_id, "readme_update", result)
            return result

    async def _run_spec_update(self, commit_sha: str, branch: str, run_id: str) -> Dict[str, Any]:
        """Run spec.md update task."""
        try:
            logger.info("Task 3: Updating spec.md...")
            # Call async method directly
            updated_spec = await self.spec_updater.update_spec(
                commit_sha=commit_sha, branch=branch
            )

            # Check if result is an error dict (rate limit, etc.)
            if isinstance(updated_spec, dict) and not updated_spec.get("success", True):
                error_type = updated_spec.get("error_type", "unknown")
                error_msg = updated_spec.get("message", "Unknown error")
                # Mark task as failed in session memory
                self.session_memory.mark_task_failed(run_id, "spec_update", error_msg, error_type)
                result = {
                    "success": False,
                    "status": "failed",
                    "error_type": error_type,
                    "message": error_msg
                }
                self.session_memory.update_task_result(run_id, "spec_update", result)
                return result

            if updated_spec:
                if self.config.CREATE_PR:
                    # Note: In parallel execution, we can't easily append to the README PR
                    # because we don't know if it exists yet.
                    # For simplicity in this async version, we'll create a separate PR or
                    # try to find an existing one (omitted for brevity, creating new one).
                    pr_result = await self._create_documentation_pr(
                        branch=branch,
                        spec_content=updated_spec,
                        commit_sha=commit_sha,
                    )
                    result = {
                        "success": pr_result["success"],
                        "status": "completed",
                        "pr_created": pr_result["success"],
                        "pr_number": pr_result.get("pr_number"),
                    }
                elif self.config.AUTO_COMMIT:
                    commit_success = await self.github.update_file(
                        file_path="spec.md",
                        content=updated_spec,
                        message=f"docs: Auto-update spec.md from {commit_sha[:7]}",
                        branch=branch,
                    )
                    result = {
                        "success": commit_success,
                        "status": "completed" if commit_success else "failed",
                        "auto_committed": commit_success,
                    }
                else:
                    result = {
                        "success": True,
                        "status": "completed",
                        "note": "Updates generated but not committed",
                    }
            else:
                result = {
                    "success": True,
                    "status": "skipped",
                    "reason": "No updates needed",
                }
            
            self.session_memory.update_task_result(run_id, "spec_update", result)
            return result
        except Exception as e:
            logger.error(f"Spec update failed: {e}", exc_info=True)
            result = {"success": False, "status": "error", "error": str(e)}
            self.session_memory.update_task_result(run_id, "spec_update", result)
            return result

    async def _create_documentation_pr(
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
            if not await self.github.create_branch(pr_branch, from_branch=branch):
                return {"success": False, "error": "Failed to create branch"}

            # Commit files
            if readme_content:
                if not await self.github.update_file(
                    file_path="README.md",
                    content=readme_content,
                    message=f"docs: Auto-update README.md from {commit_sha[:7]}",
                    branch=pr_branch,
                ):
                    return {"success": False, "error": "Failed to update README.md"}

            if spec_content:
                if not await self.github.update_file(
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

            pr_number = await self.github.create_pull_request(
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

    async def run_automation_with_context(
        self,
        event_type: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process an event with full trigger context and filtering.
        
        This is the new PR-centric entry point that:
        1. Classifies the event (PR vs push)
        2. Analyzes the diff for trivial changes
        3. Skips automation for trivial changes
        4. Routes tasks based on change type
        5. Groups automation PRs for source PRs
        
        Args:
            event_type: GitHub event type (push, pull_request)
            payload: GitHub webhook payload
            
        Returns:
            Dictionary with results including trigger context
        """
        logger.info(f"[ORCHESTRATOR] run_automation_with_context called: event_type={event_type}")
        logger.info(f"[ORCHESTRATOR] Config: TRIGGER_MODE={self.config.TRIGGER_MODE}, "
                    f"ENABLE_PR_TRIGGER={self.config.ENABLE_PR_TRIGGER}, "
                    f"ENABLE_PUSH_TRIGGER={self.config.ENABLE_PUSH_TRIGGER}")
        
        # Initialize trigger filter with config
        trigger_filter = TriggerFilter(
            trivial_max_lines=self.config.TRIVIAL_MAX_LINES,
            trivial_doc_paths=self.config.TRIVIAL_DOC_PATHS,
            enable_trivial_filter=self.config.TRIVIAL_CHANGE_FILTER_ENABLED,
        )
        
        # Check if we should process this event based on trigger mode
        should_process, skip_reason = trigger_filter.should_process_event(
            event_type, self.config.TRIGGER_MODE
        )
        logger.info(f"[ORCHESTRATOR] should_process_event: {should_process}, reason={skip_reason}")
        
        if not should_process:
            logger.info(f"[ORCHESTRATOR] Event skipped by trigger mode: {skip_reason}")
            return {
                "success": True,
                "skipped": True,
                "skip_reason": skip_reason,
                "run_type": "skipped_by_trigger_mode",
            }
        
        # Get the diff content
        logger.info(f"[ORCHESTRATOR] Fetching diff for {event_type} event...")
        diff_content = await self._get_diff_for_event(event_type, payload)
        logger.info(f"[ORCHESTRATOR] Diff fetched: {len(diff_content) if diff_content else 0} chars")
        
        # Create trigger context with full analysis
        context = trigger_filter.create_trigger_context(event_type, payload, diff_content or "")
        logger.info(f"[ORCHESTRATOR] TriggerContext created: trigger_type={context.trigger_type.value}, "
                    f"run_type={context.run_type.value}, pr_number={context.pr_number}, "
                    f"commit_sha={context.commit_sha[:7] if context.commit_sha else 'N/A'}")
        
        # Generate run ID
        run_id = f"run_{context.commit_sha[:7]}_{int(asyncio.get_event_loop().time())}"
        
        # Log the run with full context
        self.session_memory.add_run(
            run_id=run_id,
            commit_sha=context.commit_sha,
            branch=context.branch,
            trigger_type=context.trigger_type.value,
            run_type=context.run_type.value,
            pr_number=context.pr_number,
            pr_title=context.pr_title,
            skip_reason=context.skip_reason,
            diff_analysis=context.diff_analysis.to_dict() if context.diff_analysis else None,
        )
        
        # Handle skipped runs
        if context.run_type in (RunType.SKIPPED_TRIVIAL_CHANGE, RunType.SKIPPED_DOCS_ONLY):
            logger.info(f"Run skipped: {context.skip_reason}")
            self.session_memory.update_run_status(
                run_id, "skipped", context.skip_reason
            )
            return {
                "success": True,
                "skipped": True,
                "skip_reason": context.skip_reason,
                "run_id": run_id,
                "run_type": context.run_type.value,
                "trigger_type": context.trigger_type.value,
                "commit_sha": context.commit_sha,
                "pr_number": context.pr_number,
            }
        
        logger.info(
            f"Starting automation for {context.trigger_type.value} "
            f"(commit: {context.commit_sha[:7]}, PR: {context.pr_number or 'N/A'})"
        )
        
        # Build task list based on context
        tasks = []
        task_names = []
        
        if context.should_run_code_review:
            tasks.append(self._run_code_review_with_context(context, run_id))
            task_names.append("code_review")
        
        if context.should_run_readme_update:
            tasks.append(self._run_readme_update(context.commit_sha, context.branch, run_id))
            task_names.append("readme_update")
        
        if context.should_run_spec_update:
            tasks.append(self._run_spec_update(context.commit_sha, context.branch, run_id))
            task_names.append("spec_update")
        
        if not tasks:
            logger.info("No tasks to run based on context")
            self.session_memory.update_run_status(run_id, "skipped", "No tasks needed")
            return {
                "success": True,
                "skipped": True,
                "skip_reason": "No tasks needed based on change analysis",
                "run_id": run_id,
                "run_type": context.run_type.value,
            }
        
        # Execute tasks in parallel
        task_results = await self._run_parallel_tasks(tasks)
        
        # Build results dictionary
        results_dict = {}
        for i, name in enumerate(task_names):
            result = task_results[i]
            if isinstance(result, Exception):
                results_dict[name] = {"success": False, "error": str(result)}
            else:
                results_dict[name] = result
        
        # Handle PR-centric grouping of automation updates
        if context.pr_number and self.config.GROUP_AUTOMATION_UPDATES:
            await self._handle_grouped_automation_pr(context, results_dict, run_id)
        
        # Check for critical failures (Jules 404, LLM 429)
        critical_failures = []
        for task_name, result in results_dict.items():
            if isinstance(result, dict):
                error_type = result.get("error_type")
                if error_type in ("jules_404", "llm_rate_limited"):
                    critical_failures.append((task_name, error_type, result.get("message", "")))
        
        # If critical failures exist, set appropriate status and skip PR creation
        if critical_failures:
            all_failed = all(
                isinstance(r, dict) and r.get("error_type") in ("jules_404", "llm_rate_limited")
                for r in results_dict.values()
            )
            status = "failed" if all_failed else "completed_with_issues"
            failure_summary = ", ".join([f"{t}:{e}" for t, e, _ in critical_failures])
            summary = f"Critical failures: {failure_summary}"
            self.session_memory.update_run_status(run_id, status, summary)
            
            logger.warning(f"Skipping PR creation due to critical failures: {summary}")
            
            return {
                "success": False,
                "run_id": run_id,
                "run_type": context.run_type.value,
                "trigger_type": context.trigger_type.value,
                "commit_sha": context.commit_sha,
                "branch": context.branch,
                "pr_number": context.pr_number,
                "tasks": results_dict,
                "status": status,
                "critical_failures": critical_failures,
                "diff_analysis": context.diff_analysis.to_dict() if context.diff_analysis else None,
            }
        
        success = all(
            r.get("success", False) for r in results_dict.values()
            if not isinstance(r, Exception)
        )
        
        status = "completed" if success else "failed"
        summary = f"Ran {len(tasks)} tasks: {', '.join(task_names)}"
        self.session_memory.update_run_status(run_id, status, summary)
        
        return {
            "success": success,
            "run_id": run_id,
            "run_type": context.run_type.value,
            "trigger_type": context.trigger_type.value,
            "commit_sha": context.commit_sha,
            "branch": context.branch,
            "pr_number": context.pr_number,
            "tasks": results_dict,
            "diff_analysis": context.diff_analysis.to_dict() if context.diff_analysis else None,
        }

    async def _get_diff_for_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
    ) -> Optional[str]:
        """Get the diff content for an event.
        
        Args:
            event_type: GitHub event type
            payload: Webhook payload
            
        Returns:
            Diff content as string, or None
        """
        if event_type == "pull_request":
            pr_number = payload.get("number")
            if pr_number:
                return await self.github.get_pull_request_diff(pr_number)
        elif event_type == "push":
            head_commit = payload.get("head_commit", {})
            commit_sha = head_commit.get("id")
            if commit_sha:
                return await self.github.get_commit_diff(commit_sha)
        return None

    async def _run_code_review_with_context(
        self,
        context: TriggerContext,
        run_id: str,
    ) -> Dict[str, Any]:
        """Run code review with PR-centric context.
        
        If triggered by a PR, posts review on the PR instead of commit.
        """
        try:
            logger.info("Task: Running code review...")
            
            # Run the review
            review_result = await self.code_reviewer.review_commit(
                commit_sha=context.commit_sha,
                post_as_issue=self.config.POST_REVIEW_AS_ISSUE,
            )
            
            review_success = review_result.get("success", False)
            review_content = review_result.get("review", "")
            
            # Post review on PR if applicable
            posted_on_pr = False
            if (review_success and review_content and 
                context.pr_number and self.config.POST_REVIEW_ON_PR):
                posted_on_pr = await self.github.post_pull_request_review(
                    pr_number=context.pr_number,
                    body=review_content,
                    event="COMMENT",
                    commit_id=context.commit_sha,
                )
            
            # Update review log
            log_updated = False
            if review_success and review_content:
                updated_log = await self.code_review_updater.update_review_log(
                    commit_sha=context.commit_sha,
                    review_content=review_content,
                    branch=context.branch,
                )
                if updated_log and self.config.AUTO_COMMIT:
                    log_updated = await self.github.update_file(
                        file_path=CodeReviewUpdater.LOG_FILE,
                        content=updated_log,
                        message=f"docs: Update automated review log for {context.commit_sha[:7]}",
                        branch=context.branch,
                    )
            
            result = {
                "success": review_success,
                "status": "completed" if review_success else "failed",
                "posted_on_pr": posted_on_pr,
                "pr_number": context.pr_number,
                "log_updated": log_updated,
            }
            self.session_memory.update_task_result(run_id, "code_review", result)
            return result
            
        except Exception as e:
            logger.error(f"Code review failed: {e}", exc_info=True)
            result = {"success": False, "status": "error", "error": str(e)}
            self.session_memory.update_task_result(run_id, "code_review", result)
            return result

    async def _handle_grouped_automation_pr(
        self,
        context: TriggerContext,
        task_results: Dict[str, Any],
        run_id: str,
    ) -> None:
        """Handle grouping automation updates into a single PR for a source PR.
        
        Instead of creating separate PRs for README and spec updates,
        this creates or updates a single automation PR for the source PR.
        """
        if not context.pr_number:
            return
        
        # Check if we have any doc updates to commit
        readme_result = task_results.get("readme_update", {})
        spec_result = task_results.get("spec_update", {})
        
        has_readme_update = readme_result.get("success") and readme_result.get("status") == "completed"
        has_spec_update = spec_result.get("success") and spec_result.get("status") == "completed"
        
        if not has_readme_update and not has_spec_update:
            return
        
        # Check for existing automation PR for this source PR
        existing = self.session_memory.find_automation_pr_for_source_pr(context.pr_number)
        
        if existing and existing.get("automation_pr_branch"):
            # Update existing automation PR branch
            automation_branch = existing["automation_pr_branch"]
            logger.info(f"Updating existing automation branch: {automation_branch}")
            # Files would be added to existing branch
        else:
            # Create new automation PR
            automation_branch = f"automation/pr-{context.pr_number}-docs"
            
            # Create the branch from the PR's base
            base_branch = context.pr_base_branch or "main"
            if await self.github.create_branch(automation_branch, from_branch=base_branch):
                # Create the PR
                pr_title = f"🤖 Automation updates for PR #{context.pr_number}"
                pr_body = f"""## Automated Documentation Updates

This PR contains automated documentation updates for PR #{context.pr_number}: {context.pr_title}

### Updates Included:
{"- ✅ README.md updated" if has_readme_update else ""}
{"- ✅ spec.md updated" if has_spec_update else ""}

### Related PR
- #{context.pr_number}

---
*This PR was created automatically by the GitHub Automation Agent.*
"""
                automation_pr_number = await self.github.create_pull_request(
                    title=pr_title,
                    body=pr_body,
                    head=automation_branch,
                    base=base_branch,
                )
                
                if automation_pr_number:
                    self.session_memory.update_automation_pr(
                        run_id, automation_pr_number, automation_branch
                    )
                    logger.info(f"Created automation PR #{automation_pr_number} for source PR #{context.pr_number}")