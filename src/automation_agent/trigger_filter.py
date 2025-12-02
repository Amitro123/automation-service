"""Trigger filtering and trivial change detection for PR-centric automation.

This module provides:
1. Event classification (PR vs push, trigger type)
2. Trivial change detection to skip unnecessary LLM calls
3. Diff analysis for intelligent task routing
"""

import fnmatch
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Set

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Type of event that triggered automation."""
    PR_OPENED = "pr_opened"
    PR_SYNCHRONIZED = "pr_synchronized"
    PR_REOPENED = "pr_reopened"
    PUSH_WITH_PR = "push_with_pr"
    PUSH_WITHOUT_PR = "push_without_pr"


class RunType(Enum):
    """Type of automation run based on change analysis."""
    FULL_AUTOMATION = "full_automation"
    PARTIAL = "partial"  # Only some tasks run (e.g., code review only)
    SKIPPED_TRIVIAL_CHANGE = "skipped_trivial_change"
    SKIPPED_DOCS_ONLY = "skipped_docs_only"
    LIGHTWEIGHT_ONLY = "lightweight_only"  # Lint/coverage only, no LLM


@dataclass
class DiffAnalysis:
    """Analysis of a diff for intelligent task routing."""
    
    total_lines_changed: int = 0
    files_changed: List[str] = field(default_factory=list)
    code_files_changed: List[str] = field(default_factory=list)
    doc_files_changed: List[str] = field(default_factory=list)
    config_files_changed: List[str] = field(default_factory=list)
    
    # Flags
    has_code_changes: bool = False
    has_doc_changes: bool = False
    has_config_changes: bool = False
    is_trivial: bool = False
    is_whitespace_only: bool = False
    
    # Reason for classification
    trivial_reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_lines_changed": self.total_lines_changed,
            "files_changed": self.files_changed,
            "code_files_changed": self.code_files_changed,
            "doc_files_changed": self.doc_files_changed,
            "config_files_changed": self.config_files_changed,
            "has_code_changes": self.has_code_changes,
            "has_doc_changes": self.has_doc_changes,
            "has_config_changes": self.has_config_changes,
            "is_trivial": self.is_trivial,
            "is_whitespace_only": self.is_whitespace_only,
            "trivial_reason": self.trivial_reason,
        }


@dataclass
class TriggerContext:
    """Context for an automation trigger event."""
    
    trigger_type: TriggerType
    run_type: RunType
    
    # Event source
    commit_sha: str = ""
    branch: str = ""
    pr_number: Optional[int] = None
    pr_title: str = ""
    pr_base_branch: str = ""
    
    # Analysis
    diff_analysis: Optional[DiffAnalysis] = None
    
    # Task routing
    should_run_code_review: bool = True
    should_run_readme_update: bool = True
    should_run_spec_update: bool = True
    
    # Skip reason if applicable
    skip_reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "trigger_type": self.trigger_type.value,
            "run_type": self.run_type.value,
            "commit_sha": self.commit_sha,
            "branch": self.branch,
            "pr_number": self.pr_number,
            "pr_title": self.pr_title,
            "pr_base_branch": self.pr_base_branch,
            "diff_analysis": self.diff_analysis.to_dict() if self.diff_analysis else None,
            "should_run_code_review": self.should_run_code_review,
            "should_run_readme_update": self.should_run_readme_update,
            "should_run_spec_update": self.should_run_spec_update,
            "skip_reason": self.skip_reason,
        }


class TriggerFilter:
    """Filters and classifies automation triggers.
    
    Responsibilities:
    1. Classify events (PR vs push)
    2. Analyze diffs for trivial changes
    3. Determine which tasks should run
    4. Provide skip reasons for dashboard display
    """
    
    # Default patterns for doc files (can be overridden via config)
    DEFAULT_DOC_PATTERNS = [
        "README.md",
        "README.rst",
        "README.txt",
        "readme.md",
        "CHANGELOG.md",
        "CHANGELOG.rst",
        "CONTRIBUTING.md",
        "LICENSE",
        "LICENSE.md",
        "docs/**",
        "doc/**",
        "*.md",
        "*.rst",
        "*.txt",
    ]
    
    # Default patterns for config files
    DEFAULT_CONFIG_PATTERNS = [
        ".env*",
        "*.yml",
        "*.yaml",
        "*.json",
        "*.toml",
        "*.ini",
        "*.cfg",
        ".gitignore",
        ".dockerignore",
        "Dockerfile",
        "docker-compose*",
        "Makefile",
        "requirements*.txt",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "package.json",
        "package-lock.json",
        "tsconfig.json",
    ]
    
    # Patterns for code files
    CODE_EXTENSIONS = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
        ".c", ".cpp", ".h", ".hpp", ".cs", ".rb", ".php", ".swift",
        ".kt", ".scala", ".sh", ".bash", ".zsh", ".ps1", ".sql",
    }
    
    def __init__(
        self,
        trivial_max_lines: int = 10,
        trivial_doc_paths: Optional[List[str]] = None,
        enable_trivial_filter: bool = True,
    ):
        """Initialize trigger filter.
        
        Args:
            trivial_max_lines: Max lines changed to consider trivial
            trivial_doc_paths: Glob patterns for doc files
            enable_trivial_filter: Whether to enable trivial change filtering
        """
        self.trivial_max_lines = trivial_max_lines
        self.trivial_doc_paths = trivial_doc_paths or self.DEFAULT_DOC_PATTERNS
        self.enable_trivial_filter = enable_trivial_filter
    
    def classify_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
    ) -> TriggerType:
        """Classify the GitHub event type.
        
        Args:
            event_type: GitHub event type header (e.g., "push", "pull_request")
            payload: Webhook payload
            
        Returns:
            TriggerType classification
        """
        if event_type == "pull_request":
            action = payload.get("action", "")
            if action == "opened":
                return TriggerType.PR_OPENED
            elif action == "synchronize":
                return TriggerType.PR_SYNCHRONIZED
            elif action == "reopened":
                return TriggerType.PR_REOPENED
            else:
                # Default to synchronized for other PR actions we handle
                return TriggerType.PR_SYNCHRONIZED
        
        elif event_type == "push":
            # Check if this push is associated with a PR
            # This would require an API call to check, so we default to push_without_pr
            # The orchestrator can update this later if it finds an associated PR
            return TriggerType.PUSH_WITHOUT_PR
        
        # Default fallback
        return TriggerType.PUSH_WITHOUT_PR
    
    def analyze_diff(self, diff_content: str) -> DiffAnalysis:
        """Analyze a diff to determine change characteristics.
        
        Args:
            diff_content: Raw git diff content
            
        Returns:
            DiffAnalysis with classification
        """
        analysis = DiffAnalysis()
        
        if not diff_content:
            analysis.is_trivial = True
            analysis.trivial_reason = "Empty diff"
            return analysis
        
        # Parse diff to extract files and line counts
        files_changed: Set[str] = set()
        total_additions = 0
        total_deletions = 0
        whitespace_only = True
        
        current_file = None
        
        for line in diff_content.split("\n"):
            # Match file headers
            if line.startswith("diff --git"):
                match = re.search(r"b/(.+)$", line)
                if match:
                    current_file = match.group(1)
                    files_changed.add(current_file)
            
            # Count additions/deletions
            elif line.startswith("+") and not line.startswith("+++"):
                total_additions += 1
                # Check if non-whitespace content
                if line[1:].strip():
                    whitespace_only = False
            elif line.startswith("-") and not line.startswith("---"):
                total_deletions += 1
                if line[1:].strip():
                    whitespace_only = False
        
        analysis.files_changed = list(files_changed)
        analysis.total_lines_changed = total_additions + total_deletions
        analysis.is_whitespace_only = whitespace_only and analysis.total_lines_changed > 0
        
        # Classify files
        for file_path in files_changed:
            if self._is_code_file(file_path):
                analysis.code_files_changed.append(file_path)
            elif self._is_doc_file(file_path):
                analysis.doc_files_changed.append(file_path)
            elif self._is_config_file(file_path):
                analysis.config_files_changed.append(file_path)
        
        analysis.has_code_changes = len(analysis.code_files_changed) > 0
        analysis.has_doc_changes = len(analysis.doc_files_changed) > 0
        analysis.has_config_changes = len(analysis.config_files_changed) > 0
        
        # Determine if trivial
        if self.enable_trivial_filter:
            analysis.is_trivial, analysis.trivial_reason = self._check_trivial(analysis)
        
        return analysis
    
    def _is_code_file(self, file_path: str) -> bool:
        """Check if file is a code file."""
        ext = "." + file_path.rsplit(".", 1)[-1] if "." in file_path else ""
        return ext.lower() in self.CODE_EXTENSIONS
    
    def _is_doc_file(self, file_path: str) -> bool:
        """Check if file matches doc patterns."""
        for pattern in self.trivial_doc_paths:
            if fnmatch.fnmatch(file_path, pattern):
                return True
            # Also check just the filename
            if fnmatch.fnmatch(file_path.split("/")[-1], pattern):
                return True
        return False
    
    def _is_config_file(self, file_path: str) -> bool:
        """Check if file matches config patterns."""
        for pattern in self.DEFAULT_CONFIG_PATTERNS:
            if fnmatch.fnmatch(file_path, pattern):
                return True
            if fnmatch.fnmatch(file_path.split("/")[-1], pattern):
                return True
        return False
    
    def _check_trivial(self, analysis: DiffAnalysis) -> tuple[bool, str]:
        """Check if changes are trivial.
        
        Args:
            analysis: DiffAnalysis to check
            
        Returns:
            Tuple of (is_trivial, reason)
        """
        # Whitespace only changes are trivial
        if analysis.is_whitespace_only:
            return True, "Whitespace-only changes"
        
        # No code changes and small doc-only changes are trivial
        if not analysis.has_code_changes:
            if analysis.total_lines_changed <= self.trivial_max_lines:
                if analysis.has_doc_changes and not analysis.has_config_changes:
                    return True, f"Doc-only changes ({analysis.total_lines_changed} lines)"
        
        # Very small changes to any file type
        if analysis.total_lines_changed <= 3:
            return True, f"Minimal changes ({analysis.total_lines_changed} lines)"
        
        return False, ""
    
    def create_trigger_context(
        self,
        event_type: str,
        payload: Dict[str, Any],
        diff_content: str,
    ) -> TriggerContext:
        """Create a complete trigger context for automation.
        
        Args:
            event_type: GitHub event type
            payload: Webhook payload
            diff_content: Raw diff content
            
        Returns:
            TriggerContext with all routing decisions
        """
        trigger_type = self.classify_event(event_type, payload)
        diff_analysis = self.analyze_diff(diff_content)
        
        # Extract event metadata
        if event_type == "pull_request":
            pr_data = payload.get("pull_request", {})
            commit_sha = pr_data.get("head", {}).get("sha", "")
            branch = pr_data.get("head", {}).get("ref", "")
            pr_number = payload.get("number")
            pr_title = pr_data.get("title", "")
            pr_base_branch = pr_data.get("base", {}).get("ref", "")
        else:
            # Push event
            head_commit = payload.get("head_commit", {})
            commit_sha = head_commit.get("id", "")
            ref = payload.get("ref", "")
            branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref
            pr_number = None
            pr_title = ""
            pr_base_branch = ""
        
        # Determine run type and task routing
        if diff_analysis.is_trivial:
            run_type = RunType.SKIPPED_TRIVIAL_CHANGE
            should_run_code_review = False
            should_run_readme_update = False
            should_run_spec_update = False
            skip_reason = f"Trivial change: {diff_analysis.trivial_reason}"
        elif not diff_analysis.has_code_changes and diff_analysis.has_doc_changes:
            # Doc-only changes that aren't trivial
            run_type = RunType.PARTIAL
            should_run_code_review = False  # No code to review
            should_run_readme_update = True  # May need to update README
            should_run_spec_update = True  # Log the doc changes
            skip_reason = ""
        else:
            # Full automation
            run_type = RunType.FULL_AUTOMATION
            should_run_code_review = diff_analysis.has_code_changes
            should_run_readme_update = True
            should_run_spec_update = True
            skip_reason = ""
        
        return TriggerContext(
            trigger_type=trigger_type,
            run_type=run_type,
            commit_sha=commit_sha,
            branch=branch,
            pr_number=pr_number,
            pr_title=pr_title,
            pr_base_branch=pr_base_branch,
            diff_analysis=diff_analysis,
            should_run_code_review=should_run_code_review,
            should_run_readme_update=should_run_readme_update,
            should_run_spec_update=should_run_spec_update,
            skip_reason=skip_reason,
        )
    
    def should_process_event(
        self,
        event_type: str,
        trigger_mode: str,
    ) -> tuple[bool, str]:
        """Check if an event should be processed based on trigger mode.
        
        Args:
            event_type: GitHub event type
            trigger_mode: Configuration trigger mode ("pr", "push", "both")
            
        Returns:
            Tuple of (should_process, reason)
        """
        if trigger_mode == "pr":
            if event_type == "pull_request":
                return True, ""
            elif event_type == "push":
                return False, "Push events disabled (TRIGGER_MODE=pr)"
        
        elif trigger_mode == "push":
            if event_type == "push":
                return True, ""
            elif event_type == "pull_request":
                return False, "PR events disabled (TRIGGER_MODE=push)"
        
        elif trigger_mode == "both":
            if event_type in ("push", "pull_request"):
                return True, ""
        
        return False, f"Unknown event type: {event_type}"
