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

    def add_run(self, run_id: str, commit_sha: str, branch: str) -> Dict[str, Any]:
        """Start a new automation run."""
        run_entry = {
            "id": run_id,
            "commit_sha": commit_sha,
            "branch": branch,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "status": "running",
            "tasks": {},
            "metrics": {},
            "summary": ""
        }
        self._memory["runs"].insert(0, run_entry) # Prepend to keep newest first
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
