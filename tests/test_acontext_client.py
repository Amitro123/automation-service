"""Tests for Acontext Long-Term Memory Client."""

import pytest
import os
import json
import tempfile
from unittest.mock import patch, AsyncMock

from automation_agent.memory.acontext_client import AcontextClient, SessionInsight


class TestAcontextClient:
    """Test suite for AcontextClient."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage file."""
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def client(self, temp_storage):
        """Create a client with temporary storage."""
        return AcontextClient(storage_path=temp_storage, enabled=True, max_lessons=3)

    @pytest.fixture
    def disabled_client(self, temp_storage):
        """Create a disabled client."""
        return AcontextClient(storage_path=temp_storage, enabled=False)

    @pytest.mark.asyncio
    async def test_start_session_success(self, client):
        """Test successfully starting a session."""
        result = await client.start_session(
            session_id="run_123",
            pr_title="feat: add user auth",
            pr_files=["src/auth.py", "tests/test_auth.py"],
            branch="main",
            pr_number=42,
        )
        
        assert result is True
        
        # Verify session was stored
        assert "run_123" in client._memory["sessions"]
        session = client._memory["sessions"]["run_123"]
        assert session["pr_title"] == "feat: add user auth"
        assert session["status"] == "running"
        assert session["pr_number"] == 42

    @pytest.mark.asyncio
    async def test_start_session_disabled(self, disabled_client):
        """Test starting session when client is disabled."""
        result = await disabled_client.start_session(
            session_id="run_123",
            pr_title="test",
            pr_files=[],
            branch="main",
        )
        
        assert result is True
        assert "run_123" not in disabled_client._memory["sessions"]

    @pytest.mark.asyncio
    async def test_log_event_success(self, client):
        """Test logging an event to a session."""
        await client.start_session(
            session_id="run_123",
            pr_title="test",
            pr_files=[],
            branch="main",
        )
        
        result = await client.log_event(
            session_id="run_123",
            event_type="code_review_complete",
            data={"issues": ["Missing docstring", "Unused import"]},
        )
        
        assert result is True
        
        session = client._memory["sessions"]["run_123"]
        assert len(session["events"]) == 1
        assert session["events"][0]["type"] == "code_review_complete"
        # Should have extracted lessons
        assert "Missing docstring" in session["key_lessons"]

    @pytest.mark.asyncio
    async def test_log_event_error_type(self, client):
        """Test logging an error event extracts error_types."""
        await client.start_session(
            session_id="run_123",
            pr_title="test",
            pr_files=[],
            branch="main",
        )
        
        await client.log_event(
            session_id="run_123",
            event_type="error",
            data={"error_type": "jules_404"},
        )
        
        session = client._memory["sessions"]["run_123"]
        assert "jules_404" in session["error_types"]

    @pytest.mark.asyncio
    async def test_finish_session_success(self, client):
        """Test finishing a session with success status."""
        await client.start_session(
            session_id="run_123",
            pr_title="test",
            pr_files=[],
            branch="main",
        )
        
        result = await client.finish_session(
            session_id="run_123",
            status="completed",
            summary="All tasks completed",
        )
        
        assert result is True
        
        session = client._memory["sessions"]["run_123"]
        assert session["status"] == "completed"
        assert session["summary"] == "All tasks completed"
        assert "finished_at" in session

    @pytest.mark.asyncio
    async def test_finish_session_with_errors(self, client):
        """Test finishing a session with error messages."""
        await client.start_session(
            session_id="run_123",
            pr_title="test",
            pr_files=[],
            branch="main",
        )
        
        await client.finish_session(
            session_id="run_123",
            status="failed",
            error_messages=["LLM rate limited", "Jules 404"],
        )
        
        session = client._memory["sessions"]["run_123"]
        assert session["status"] == "failed"
        assert "error_messages" in session
        assert len(session["key_lessons"]) >= 1

    @pytest.mark.asyncio
    async def test_query_similar_sessions_empty(self, client):
        """Test querying when no sessions exist."""
        results = await client.query_similar_sessions(
            pr_title="feat: add feature",
            pr_files=["src/feature.py"],
        )
        
        assert results == []

    @pytest.mark.asyncio
    async def test_query_similar_sessions_with_matches(self, client):
        """Test querying for similar sessions."""
        # Create a completed session with lessons
        await client.start_session(
            session_id="run_old",
            pr_title="feat: add authentication",
            pr_files=["src/auth.py"],
            branch="main",
        )
        await client.log_event(
            "run_old",
            "code_review_complete",
            {"issues": ["Missing type hints"]},
        )
        await client.finish_session(
            "run_old",
            status="completed",
            summary="Done",
        )
        
        # Query for similar session
        results = await client.query_similar_sessions(
            pr_title="feat: add authentication module",
            pr_files=["src/auth.py"],
        )
        
        assert len(results) == 1
        assert results[0].session_id == "run_old"
        assert results[0].similarity_score > 0

    @pytest.mark.asyncio
    async def test_query_excludes_running_sessions(self, client):
        """Test that running sessions are excluded from queries."""
        await client.start_session(
            session_id="run_running",
            pr_title="feat: add feature",
            pr_files=["src/feature.py"],
            branch="main",
        )
        # Don't finish it - it's still running
        
        results = await client.query_similar_sessions(
            pr_title="feat: add feature",
            pr_files=["src/feature.py"],
        )
        
        assert results == []

    def test_format_lessons_for_prompt_empty(self, client):
        """Test formatting when no insights provided."""
        result = client.format_lessons_for_prompt([])
        assert result == ""

    def test_format_lessons_for_prompt_with_insights(self, client):
        """Test formatting insights into prompt string."""
        insights = [
            SessionInsight(
                session_id="run_1",
                pr_title="Add auth",
                timestamp="2024-01-01T00:00:00Z",
                status="completed",
                key_lessons=["Always add type hints"],
                error_types=[],
                files_changed=["auth.py"],
                similarity_score=0.8,
            )
        ]
        
        result = client.format_lessons_for_prompt(insights)
        
        assert "Lessons from Similar Past Reviews" in result
        assert "Add auth" in result
        assert "Always add type hints" in result

    def test_get_stats(self, client):
        """Test getting memory statistics."""
        stats = client.get_stats()
        
        assert "total_sessions" in stats
        assert "storage_path" in stats
        assert "enabled" in stats
        assert stats["enabled"] is True

    @pytest.mark.asyncio
    async def test_fail_safe_on_storage_error(self, client):
        """Test fail-safe behavior when storage is inaccessible."""
        # Make storage path invalid
        client.storage_path = "/invalid/path/that/does/not/exist.json"
        
        # All operations should return gracefully
        result = await client.start_session(
            session_id="run_123",
            pr_title="test",
            pr_files=[],
            branch="main",
        )
        # Should return False but not raise
        assert result is False

    @pytest.mark.asyncio
    async def test_session_insight_serialization(self):
        """Test SessionInsight to_dict and from_dict."""
        insight = SessionInsight(
            session_id="run_1",
            pr_title="Test PR",
            timestamp="2024-01-01",
            status="completed",
            key_lessons=["Lesson 1"],
            error_types=["error_1"],
            files_changed=["file.py"],
            similarity_score=0.5,
        )
        
        as_dict = insight.to_dict()
        assert as_dict["session_id"] == "run_1"
        
        restored = SessionInsight.from_dict(as_dict)
        assert restored.session_id == "run_1"
        assert restored.pr_title == "Test PR"
