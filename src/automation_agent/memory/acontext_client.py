"""
Acontext Client - Long-term memory layer for the automation agent.

This module provides an async client for Acontext that enables the agent
to learn from past PRs and improve over time. Uses real Acontext API
with local JSON fallback when the service is unreachable.

API Reference: http://localhost:8029/api/v1
"""

import json
import logging
import os
import aiohttp
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class SessionInsight:
    """Represents a lesson learned from a past session."""
    session_id: str
    pr_title: str
    timestamp: str
    status: str
    key_lessons: List[str]
    error_types: List[str]
    files_changed: List[str]
    similarity_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionInsight":
        """Create from dictionary."""
        return cls(
            session_id=data.get("session_id", ""),
            pr_title=data.get("pr_title", ""),
            timestamp=data.get("timestamp", ""),
            status=data.get("status", ""),
            key_lessons=data.get("key_lessons", []),
            error_types=data.get("error_types", []),
            files_changed=data.get("files_changed", []),
            similarity_score=data.get("similarity_score", 0.0),
        )


class AcontextClient:
    """
    Async client for Acontext long-term memory.
    
    Provides methods to:
    - Start sessions when automation runs begin
    - Log events during the run
    - Finish sessions with final status
    - Query similar past sessions for learning
    
    Uses real Acontext API with local JSON fallback.
    """
    
    def __init__(
        self,
        api_url: str = "http://localhost:8029/api/v1",
        storage_path: str = "acontext_memory.json",
        enabled: bool = True,
        max_lessons: int = 5,
    ):
        """
        Initialize Acontext client.
        
        Args:
            api_url: URL of Acontext API
            storage_path: Path to local JSON storage (fallback)
            enabled: Whether Acontext is enabled
            max_lessons: Maximum lessons to return from queries
        """
        self.api_url = api_url.rstrip("/")
        self.storage_path = storage_path
        self.enabled = enabled
        self.max_lessons = max_lessons
        self._memory: Dict[str, Any] = {"sessions": {}, "metadata": {}}
        self._api_available: Optional[bool] = None
        self._load_memory()
        
    def _load_memory(self) -> None:
        """Load local fallback memory from disk."""
        if not self.enabled:
            return
            
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self._memory = json.load(f)
                logger.debug(f"[ACONTEXT] Loaded {len(self._memory.get('sessions', {}))} sessions from local fallback")
        except Exception as e:
            logger.warning(f"[ACONTEXT] Failed to load local memory: {e}")
            self._memory = {"sessions": {}, "metadata": {}}
    
    def _save_memory(self) -> bool:
        """Save local fallback memory to disk."""
        if not self.enabled:
            return True
            
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self._memory, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.warning(f"[ACONTEXT] Failed to save local memory: {e}")
            return False

    async def _api_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request to Acontext API."""
        url = f"{self.api_url}{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                if method == "GET":
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status == 200:
                            self._api_available = True
                            return await resp.json()
                        else:
                            logger.warning(f"[ACONTEXT] API returned {resp.status} for GET {endpoint}")
                            return None
                elif method == "POST":
                    async with session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status in (200, 201):
                            self._api_available = True
                            return await resp.json()
                        else:
                            logger.warning(f"[ACONTEXT] API returned {resp.status} for POST {endpoint}")
                            return None
                elif method == "PUT":
                    async with session.put(url, json=data, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status == 200:
                            self._api_available = True
                            return await resp.json()
                        else:
                            logger.warning(f"[ACONTEXT] API returned {resp.status} for PUT {endpoint}")
                            return None
        except aiohttp.ClientError as e:
            if self._api_available is not False:
                logger.info(f"[ACONTEXT] API unavailable ({e}), using local fallback")
                self._api_available = False
            return None
        except Exception as e:
            logger.warning(f"[ACONTEXT] API request failed: {e}")
            return None
    
    async def start_session(
        self,
        session_id: str,
        pr_title: str,
        pr_files: List[str],
        branch: str,
        pr_number: Optional[int] = None,
    ) -> bool:
        """
        Start a new Acontext session.
        
        Args:
            session_id: Unique session identifier (usually run_id)
            pr_title: Title of the PR or commit message
            pr_files: List of files changed
            branch: Branch name
            pr_number: PR number if applicable
            
        Returns:
            True if session started successfully
        """
        if not self.enabled:
            logger.debug("[ACONTEXT] Disabled, skipping start_session")
            return True
            
        session_data = {
            "session_id": session_id,
            "pr_title": pr_title,
            "pr_files": pr_files,
            "branch": branch,
            "pr_number": pr_number,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "running",
            "events": [],
            "key_lessons": [],
            "error_types": [],
        }
        
        # Try API first
        result = await self._api_request("POST", "/sessions", session_data)
        if result:
            logger.info(f"[ACONTEXT] Started session {session_id} via API")
            return True
        
        # Fallback to local storage
        try:
            self._memory["sessions"][session_id] = session_data
            success = self._save_memory()
            if success:
                logger.info(f"[ACONTEXT] Started session {session_id} (local fallback)")
            return success
        except Exception as e:
            logger.warning(f"[ACONTEXT] Failed to start session: {e}")
            return False
    
    async def log_event(
        self,
        session_id: str,
        event_type: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Log an event to the current session.
        
        Args:
            session_id: Session identifier
            event_type: Type of event (e.g., "code_review_complete", "error")
            data: Event data
            
        Returns:
            True if event logged successfully
        """
        if not self.enabled:
            return True
            
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "data": data,
        }
        
        # Try API first
        result = await self._api_request(
            "POST", 
            f"/sessions/{session_id}/events", 
            event
        )
        if result:
            return True
        
        # Fallback to local storage
        try:
            session = self._memory["sessions"].get(session_id)
            if not session:
                session = {"session_id": session_id, "events": [], "key_lessons": [], "error_types": []}
                self._memory["sessions"][session_id] = session
            
            session["events"].append(event)
            
            # Extract lessons from certain event types
            if event_type == "code_review_complete":
                if data.get("issues"):
                    session["key_lessons"].extend(data["issues"][:3])
            elif event_type == "error":
                error_type = data.get("error_type", "unknown")
                if error_type not in session["error_types"]:
                    session["error_types"].append(error_type)
            
            return self._save_memory()
        except Exception as e:
            logger.warning(f"[ACONTEXT] Failed to log event: {e}")
            return False
    
    async def finish_session(
        self,
        session_id: str,
        status: str,
        error_messages: List[str] = None,
        summary: str = "",
    ) -> bool:
        """
        Finish a session with final status.
        
        Args:
            session_id: Session identifier
            status: Final status (success, failed, completed_with_issues)
            error_messages: List of error messages if any
            summary: Summary of the run
            
        Returns:
            True if session finished successfully
        """
        if not self.enabled:
            return True
            
        finish_data = {
            "status": status,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "error_messages": error_messages or [],
        }
        
        # Try API first
        result = await self._api_request(
            "PUT",
            f"/sessions/{session_id}",
            finish_data
        )
        if result:
            logger.info(f"[ACONTEXT] Finished session {session_id} via API: {status}")
            return True
        
        # Fallback to local storage
        try:
            session = self._memory["sessions"].get(session_id)
            if not session:
                return True
            
            session["status"] = status
            session["finished_at"] = finish_data["finished_at"]
            session["summary"] = summary
            
            if error_messages:
                session["error_messages"] = error_messages
                for msg in error_messages[:2]:
                    lesson = f"Error encountered: {msg[:100]}"
                    if lesson not in session["key_lessons"]:
                        session["key_lessons"].append(lesson)
            
            success = self._save_memory()
            if success:
                logger.info(f"[ACONTEXT] Finished session {session_id} (local): {status}")
            return success
        except Exception as e:
            logger.warning(f"[ACONTEXT] Failed to finish session: {e}")
            return False
    
    async def query_similar_sessions(
        self,
        pr_title: str,
        pr_files: List[str],
        limit: Optional[int] = None,
    ) -> List[SessionInsight]:
        """
        Query for similar past sessions based on PR title and files.
        
        Args:
            pr_title: Title of current PR
            pr_files: Files changed in current PR
            limit: Maximum results to return
            
        Returns:
            List of SessionInsight objects sorted by relevance
        """
        if not self.enabled:
            return []
            
        limit = limit or self.max_lessons
        
        # Try API first
        query_params = {
            "pr_title": pr_title,
            "pr_files": pr_files,
            "limit": limit,
        }
        result = await self._api_request("POST", "/sessions/query", query_params)
        if result and isinstance(result, list):
            insights = [SessionInsight.from_dict(item) for item in result]
            logger.info(f"[ACONTEXT] Found {len(insights)} similar sessions via API")
            return insights
        
        # Fallback to local similarity search
        return self._local_similarity_search(pr_title, pr_files, limit)
    
    def _local_similarity_search(
        self,
        pr_title: str,
        pr_files: List[str],
        limit: int,
    ) -> List[SessionInsight]:
        """Local fallback for similarity search."""
        try:
            insights = []
            title_words = set(pr_title.lower().split())
            file_patterns = set()
            for f in pr_files:
                parts = f.replace("\\", "/").split("/")
                file_patterns.update(parts)
                if "." in f:
                    file_patterns.add(f.split(".")[-1])
            
            for session_id, session in self._memory.get("sessions", {}).items():
                if session.get("status") == "running":
                    continue
                if not session.get("key_lessons"):
                    continue
                
                score = 0.0
                session_title_words = set(session.get("pr_title", "").lower().split())
                title_overlap = len(title_words & session_title_words)
                if title_words:
                    score += (title_overlap / len(title_words)) * 0.5
                
                session_files = session.get("pr_files", [])
                session_patterns = set()
                for f in session_files:
                    parts = f.replace("\\", "/").split("/")
                    session_patterns.update(parts)
                    if "." in f:
                        session_patterns.add(f.split(".")[-1])
                
                if file_patterns:
                    file_overlap = len(file_patterns & session_patterns)
                    score += (file_overlap / len(file_patterns)) * 0.5
                
                if score > 0.1:
                    insight = SessionInsight(
                        session_id=session_id,
                        pr_title=session.get("pr_title", ""),
                        timestamp=session.get("finished_at", session.get("started_at", "")),
                        status=session.get("status", ""),
                        key_lessons=session.get("key_lessons", [])[:3],
                        error_types=session.get("error_types", []),
                        files_changed=session_files[:5],
                        similarity_score=score,
                    )
                    insights.append(insight)
            
            insights.sort(key=lambda x: x.similarity_score, reverse=True)
            result = insights[:limit]
            
            if result:
                logger.info(f"[ACONTEXT] Found {len(result)} similar sessions (local fallback)")
            return result
        except Exception as e:
            logger.warning(f"[ACONTEXT] Local search failed: {e}")
            return []
    
    def format_lessons_for_prompt(self, insights: List[SessionInsight]) -> str:
        """Format session insights into a string for LLM prompts."""
        if not insights:
            return ""
        
        lines = ["### Lessons from Similar Past Reviews:"]
        
        for i, insight in enumerate(insights, 1):
            lines.append(f"\n**{i}. {insight.pr_title[:60]}** (status: {insight.status})")
            
            if insight.key_lessons:
                for lesson in insight.key_lessons[:2]:
                    lines.append(f"   - {lesson[:150]}")
            
            if insight.error_types:
                lines.append(f"   - Errors encountered: {', '.join(insight.error_types[:3])}")
        
        lines.append("\n---")
        return "\n".join(lines)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored sessions."""
        sessions = self._memory.get("sessions", {})
        
        status_counts = {}
        for session in sessions.values():
            status = session.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_sessions": len(sessions),
            "status_breakdown": status_counts,
            "api_url": self.api_url,
            "api_available": self._api_available,
            "storage_path": self.storage_path,
            "enabled": self.enabled,
        }
