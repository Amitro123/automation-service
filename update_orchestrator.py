"""Script to update orchestrator.py with critical failure handling."""

# Read the original file
with open("src/automation_agent/orchestrator.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add import for RateLimitError at the top
import_section = '''from .trigger_filter import TriggerFilter, TriggerContext, TriggerType, RunType

logger = logging.getLogger(__name__)'''

new_import_section = '''from .trigger_filter import TriggerFilter, TriggerContext, TriggerType, RunType
from .llm_client import RateLimitError

logger = logging.getLogger(__name__)'''

content = content.replace(import_section, new_import_section)

# 2. Update _run_code_review to handle structured errors
old_code_review = '''            review_success = review_result.get("success", False)
            review_content = review_result.get("review", "")
            
            log_updated = False
            if review_success and review_content:'''

new_code_review = '''            review_success = review_result.get("success", False)
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
            if review_success and review_content:'''

content = content.replace(old_code_review, new_code_review)

# 3. Update run_automation_with_context to check for critical failures
old_automation_context = '''        success = all(
            r.get("success", False) for r in results_dict.values()
            if not isinstance(r, Exception)
        )
        
        status = "completed" if success else "failed"
        summary = f"Ran {len(tasks)} tasks: {', '.join(task_names)}"
        self.session_memory.update_run_status(run_id, status, summary)
        
        return {'''

new_automation_context = '''        # Check for critical failures (Jules 404, LLM 429)
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
        
        return {'''

content = content.replace(old_automation_context, new_automation_context)

# Write the updated content
with open("src/automation_agent/orchestrator.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✓ Successfully updated orchestrator.py with critical failure handling")
