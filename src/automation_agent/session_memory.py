import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class SessionMemoryStore:
    """
    Persists session data (runs, metrics, logs) to a JSON file.
    Acts as the 'brain' memory for the automation agent.
    """

    def __init__(self, storage_path: str = "session_memory.json"):
        self.storage_path = storage_path
        self._memory: Dict[str, Any] = {
            "runs": [],
            "metrics": {
                "total_tokens": 0,
                "total_cost": 0.0,
                "total_runs": 0
            }
        }
        self._load()

    def _load(self):
        """Load memory from disk."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self._memory = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load session memory: {e}")
                # Keep default empty memory

    def _save(self):
        """Save memory to disk."""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self._memory, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save session memory: {e}")

    def add_run(
        self,
        run_id: str,
        commit_sha: str,
        branch: str,
        trigger_type: str = "push_without_pr",
        run_type: str = "full_automation",
        pr_number: Optional[int] = None,
        pr_title: str = "",
        skip_reason: str = "",
        diff_analysis: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Start a new automation run.
        
        Args:
            run_id: Unique run identifier
            commit_sha: Git commit SHA
            branch: Branch name
            trigger_type: Type of trigger (pr_opened, pr_synchronized, push_without_pr, etc.)
            run_type: Type of run (full_automation, partial, skipped_trivial_change, etc.)
            pr_number: Associated PR number if triggered by PR
            pr_title: PR title if triggered by PR
            skip_reason: Reason for skipping if run_type is skipped
            diff_analysis: Analysis of the diff for this run
        """
        run_entry = {
            "id": run_id,
            "commit_sha": commit_sha,
            "branch": branch,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "status": "running",
            "tasks": {},
            "metrics": {},
            "summary": "",
            # New PR-centric fields
            "trigger_type": trigger_type,
            "run_type": run_type,
            "pr_number": pr_number,
            "pr_title": pr_title,
            "skip_reason": skip_reason,
            "diff_analysis": diff_analysis,
            # Track automation PR created for this source PR
            "automation_pr_number": None,
            "automation_pr_branch": None,
            # Track task-level failures
            "failed_tasks": [],  # List of task names that failed
            "failure_reasons": {},  # Dict of task_name -> failure reason
        }
        self._memory["runs"].insert(0, run_entry)  # Prepend to keep newest first
        self._memory["metrics"]["total_runs"] += 1
        self._save()
        return run_entry

    def update_run_status(self, run_id: str, status: str, summary: str = ""):
        """Update the status of a run."""
        for run in self._memory["runs"]:
            if run["id"] == run_id:
                run["status"] = status
                if summary:
                    run["summary"] = summary
                if status in ["completed", "failed", "error"]:
                    run["end_time"] = datetime.now(timezone.utc).isoformat()
                self._save()
                return
        logger.warning(f"Run ID {run_id} not found for status update.")

    def update_task_result(self, run_id: str, task_name: str, result: Dict[str, Any]):
        """Update the result of a specific task within a run."""
        for run in self._memory["runs"]:
            if run["id"] == run_id:
                run["tasks"][task_name] = result
                self._save()
                return
        logger.warning(f"Run ID {run_id} not found for task update.")

    def add_metric(self, run_id: str, metric_name: str, value: Any):
        """Add a metric to a run and update global totals if applicable."""
        for run in self._memory["runs"]:
            if run["id"] == run_id:
                run["metrics"][metric_name] = value
                
                # Update global counters
                if metric_name == "tokens_used":
                    self._memory["metrics"]["total_tokens"] += int(value)
                elif metric_name == "estimated_cost":
                    self._memory["metrics"]["total_cost"] += float(value)
                
                self._save()
                return
        logger.warning(f"Run ID {run_id} not found for metric update.")

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent run history."""
        return self._memory["runs"][:limit]

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific run by ID."""
        for run in self._memory["runs"]:
            if run["id"] == run_id:
                return run
        return None

    def get_global_metrics(self) -> Dict[str, Any]:
        """Get global accumulated metrics."""
        return self._memory["metrics"]

    def update_automation_pr(
        self,
        run_id: str,
        automation_pr_number: int,
        automation_pr_branch: str,
    ) -> None:
        """Update the automation PR info for a run.
        
        Args:
            run_id: Run ID to update
            automation_pr_number: PR number of the automation PR
            automation_pr_branch: Branch name of the automation PR
        """
        for run in self._memory["runs"]:
            if run["id"] == run_id:
                run["automation_pr_number"] = automation_pr_number
                run["automation_pr_branch"] = automation_pr_branch
                self._save()
                return
        logger.warning(f"Run ID {run_id} not found for automation PR update.")

    def find_automation_pr_for_source_pr(self, source_pr_number: int) -> Optional[Dict[str, Any]]:
        """Find an existing automation PR for a source PR.
        
        Args:
            source_pr_number: The source PR number to find automation PR for
            
        Returns:
            Run entry with automation PR info, or None if not found
        """
        for run in self._memory["runs"]:
            if (run.get("pr_number") == source_pr_number and 
                run.get("automation_pr_number") is not None):
                return run
        return None

    def get_runs_by_pr(self, pr_number: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get runs associated with a specific PR.
        
        Args:
            pr_number: PR number to filter by
            limit: Maximum number of runs to return
            
        Returns:
            List of run entries for the PR
        """
        runs = [
            run for run in self._memory["runs"]
            if run.get("pr_number") == pr_number
        ]
        return runs[:limit]

    def mark_task_failed(
        self,
        run_id: str,
        task_name: str,
        reason: str,
        error_type: str
    ) -> None:
        """Mark a specific task as failed with a reason.
        
        Args:
            run_id: Run ID to update
            task_name: Name of the failed task
            reason: Human-readable failure reason
            error_type: Machine-readable error type (jules_404, llm_rate_limited, etc.)
        """
        for run in self._memory["runs"]:
            if run["id"] == run_id:
                if "failed_tasks" not in run:
                    run["failed_tasks"] = []
                if "failure_reasons" not in run:
                    run["failure_reasons"] = {}
                
                if task_name not in run["failed_tasks"]:
                    run["failed_tasks"].append(task_name)
                run["failure_reasons"][task_name] = {
                    "reason": reason,
                    "error_type": error_type
                }
                self._save()
                return
        logger.warning(f"Run ID {run_id} not found for marking task failed.")

    def get_skipped_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get runs that were skipped due to trivial changes.
        
        Args:
            limit: Maximum number of runs to return
            
        Returns:
            List of skipped run entries
        """
        skipped = [
            run for run in self._memory["runs"]
            if run.get("run_type", "").startswith("skipped")
        ]
        return skipped[:limit]
