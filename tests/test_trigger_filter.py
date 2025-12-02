"""Tests for trigger_filter.py - Trivial change detection and event classification."""

import pytest
from automation_agent.trigger_filter import (
    TriggerFilter,
    TriggerContext,
    TriggerType,
    RunType,
    DiffAnalysis,
)


class TestTriggerFilter:
    """Tests for TriggerFilter class."""

    def test_classify_event_push(self):
        """Test classification of push events."""
        filter = TriggerFilter()
        payload = {"ref": "refs/heads/main"}
        
        result = filter.classify_event("push", payload)
        
        assert result == TriggerType.PUSH_WITHOUT_PR

    def test_classify_event_pr_opened(self):
        """Test classification of PR opened events."""
        filter = TriggerFilter()
        payload = {"action": "opened", "number": 123}
        
        result = filter.classify_event("pull_request", payload)
        
        assert result == TriggerType.PR_OPENED

    def test_classify_event_pr_synchronized(self):
        """Test classification of PR synchronized events."""
        filter = TriggerFilter()
        payload = {"action": "synchronize", "number": 123}
        
        result = filter.classify_event("pull_request", payload)
        
        assert result == TriggerType.PR_SYNCHRONIZED

    def test_classify_event_pr_reopened(self):
        """Test classification of PR reopened events."""
        filter = TriggerFilter()
        payload = {"action": "reopened", "number": 123}
        
        result = filter.classify_event("pull_request", payload)
        
        assert result == TriggerType.PR_REOPENED


class TestDiffAnalysis:
    """Tests for diff analysis functionality."""

    def test_analyze_empty_diff(self):
        """Test analysis of empty diff."""
        filter = TriggerFilter()
        
        result = filter.analyze_diff("")
        
        assert result.is_trivial is True
        assert result.trivial_reason == "Empty diff"

    def test_analyze_code_file_changes(self):
        """Test analysis of code file changes."""
        filter = TriggerFilter()
        diff = """diff --git a/src/main.py b/src/main.py
--- a/src/main.py
+++ b/src/main.py
@@ -1,5 +1,10 @@
+import logging
+
 def main():
-    print("hello")
+    logging.info("Starting application")
+    print("hello world")
+    return 0
"""
        
        result = filter.analyze_diff(diff)
        
        assert result.has_code_changes is True
        assert "src/main.py" in result.code_files_changed
        assert result.is_trivial is False

    def test_analyze_doc_only_small_changes(self):
        """Test analysis of small doc-only changes (should be trivial)."""
        filter = TriggerFilter(trivial_max_lines=10)
        diff = """diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1,3 +1,5 @@
 # Project
+New section added here.
+More content.
 Description here.
"""
        
        result = filter.analyze_diff(diff)
        
        assert result.has_doc_changes is True
        assert result.has_code_changes is False
        assert result.is_trivial is True
        # Could be "Doc-only" or "Minimal" depending on line count
        assert result.trivial_reason != ""

    def test_analyze_doc_large_changes(self):
        """Test analysis of large doc changes (should not be trivial)."""
        filter = TriggerFilter(trivial_max_lines=5)
        diff = """diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1,3 +1,20 @@
 # Project
+
+## Features
+- Feature 1
+- Feature 2
+- Feature 3
+
+## Installation
+Run pip install
+
+## Usage
+Import and use
+
+## Contributing
+Please read CONTRIBUTING.md
+
+## License
+MIT
"""
        
        result = filter.analyze_diff(diff)
        
        assert result.has_doc_changes is True
        assert result.total_lines_changed > 5
        assert result.is_trivial is False

    def test_analyze_whitespace_only(self):
        """Test analysis of whitespace-only changes."""
        filter = TriggerFilter()
        # Pure whitespace additions (empty lines only)
        diff = """diff --git a/src/main.py b/src/main.py
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,5 @@
 def main():
+
+
     pass
"""
        
        result = filter.analyze_diff(diff)
        
        # Whitespace-only should be trivial
        assert result.is_whitespace_only is True
        assert result.is_trivial is True

    def test_analyze_minimal_changes(self):
        """Test analysis of minimal changes (<=3 lines)."""
        filter = TriggerFilter()
        diff = """diff --git a/src/main.py b/src/main.py
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
 def main():
+    # Added comment
     pass
"""
        
        result = filter.analyze_diff(diff)
        
        assert result.total_lines_changed <= 3
        assert result.is_trivial is True
        assert "Minimal" in result.trivial_reason


class TestTriggerContext:
    """Tests for trigger context creation."""

    def test_create_context_push_event(self):
        """Test context creation for push event."""
        filter = TriggerFilter()
        payload = {
            "ref": "refs/heads/feature-branch",
            "head_commit": {
                "id": "abc123def456",
                "message": "feat: add new feature",
            },
        }
        diff = """diff --git a/src/main.py b/src/main.py
+import os
+def new_function():
+    return os.getcwd()
"""
        
        context = filter.create_trigger_context("push", payload, diff)
        
        assert context.trigger_type == TriggerType.PUSH_WITHOUT_PR
        assert context.commit_sha == "abc123def456"
        assert context.branch == "feature-branch"
        assert context.pr_number is None

    def test_create_context_pr_event(self):
        """Test context creation for PR event."""
        filter = TriggerFilter()
        payload = {
            "action": "opened",
            "number": 42,
            "pull_request": {
                "title": "Add new feature",
                "head": {
                    "sha": "abc123def456",
                    "ref": "feature-branch",
                },
                "base": {
                    "ref": "main",
                },
            },
        }
        diff = """diff --git a/src/main.py b/src/main.py
+import os
+def new_function():
+    return os.getcwd()
"""
        
        context = filter.create_trigger_context("pull_request", payload, diff)
        
        assert context.trigger_type == TriggerType.PR_OPENED
        assert context.commit_sha == "abc123def456"
        assert context.branch == "feature-branch"
        assert context.pr_number == 42
        assert context.pr_title == "Add new feature"
        assert context.pr_base_branch == "main"

    def test_create_context_trivial_change_skips_tasks(self):
        """Test that trivial changes result in skipped tasks."""
        filter = TriggerFilter(trivial_max_lines=10)
        payload = {
            "ref": "refs/heads/main",
            "head_commit": {"id": "abc123", "message": "docs: fix typo"},
        }
        # Small README change
        diff = """diff --git a/README.md b/README.md
+Fixed typo
"""
        
        context = filter.create_trigger_context("push", payload, diff)
        
        assert context.run_type == RunType.SKIPPED_TRIVIAL_CHANGE
        assert context.should_run_code_review is False
        assert context.should_run_readme_update is False
        assert context.should_run_spec_update is False
        assert context.skip_reason != ""

    def test_create_context_code_changes_runs_all_tasks(self):
        """Test that code changes result in full automation."""
        filter = TriggerFilter()
        payload = {
            "ref": "refs/heads/main",
            "head_commit": {"id": "abc123", "message": "feat: add feature"},
        }
        diff = """diff --git a/src/feature.py b/src/feature.py
+def new_feature():
+    return "Hello"
+
+def another_function():
+    return 42
"""
        
        context = filter.create_trigger_context("push", payload, diff)
        
        assert context.run_type == RunType.FULL_AUTOMATION
        assert context.should_run_code_review is True
        assert context.should_run_readme_update is True
        assert context.should_run_spec_update is True


class TestTriggerModeFiltering:
    """Tests for trigger mode filtering."""

    def test_pr_mode_accepts_pr_events(self):
        """Test that PR mode accepts PR events."""
        filter = TriggerFilter()
        
        should_process, reason = filter.should_process_event("pull_request", "pr")
        
        assert should_process is True
        assert reason == ""

    def test_pr_mode_rejects_push_events(self):
        """Test that PR mode rejects push events."""
        filter = TriggerFilter()
        
        should_process, reason = filter.should_process_event("push", "pr")
        
        assert should_process is False
        assert "Push events disabled" in reason

    def test_push_mode_accepts_push_events(self):
        """Test that push mode accepts push events."""
        filter = TriggerFilter()
        
        should_process, reason = filter.should_process_event("push", "push")
        
        assert should_process is True
        assert reason == ""

    def test_push_mode_rejects_pr_events(self):
        """Test that push mode rejects PR events."""
        filter = TriggerFilter()
        
        should_process, reason = filter.should_process_event("pull_request", "push")
        
        assert should_process is False
        assert "PR events disabled" in reason

    def test_both_mode_accepts_all_events(self):
        """Test that 'both' mode accepts all events."""
        filter = TriggerFilter()
        
        should_process_push, _ = filter.should_process_event("push", "both")
        should_process_pr, _ = filter.should_process_event("pull_request", "both")
        
        assert should_process_push is True
        assert should_process_pr is True


class TestDiffAnalysisToDict:
    """Tests for DiffAnalysis serialization."""

    def test_to_dict(self):
        """Test DiffAnalysis to_dict method."""
        analysis = DiffAnalysis(
            total_lines_changed=10,
            files_changed=["file1.py", "file2.py"],
            code_files_changed=["file1.py"],
            doc_files_changed=["README.md"],
            has_code_changes=True,
            has_doc_changes=True,
            is_trivial=False,
        )
        
        result = analysis.to_dict()
        
        assert result["total_lines_changed"] == 10
        assert result["files_changed"] == ["file1.py", "file2.py"]
        assert result["has_code_changes"] is True
        assert result["is_trivial"] is False


class TestTriggerContextToDict:
    """Tests for TriggerContext serialization."""

    def test_to_dict(self):
        """Test TriggerContext to_dict method."""
        context = TriggerContext(
            trigger_type=TriggerType.PR_OPENED,
            run_type=RunType.FULL_AUTOMATION,
            commit_sha="abc123",
            branch="main",
            pr_number=42,
            pr_title="Test PR",
        )
        
        result = context.to_dict()
        
        assert result["trigger_type"] == "pr_opened"
        assert result["run_type"] == "full_automation"
        assert result["commit_sha"] == "abc123"
        assert result["pr_number"] == 42
