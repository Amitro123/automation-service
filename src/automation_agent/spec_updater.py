"""Automated spec.md project documentation module."""

import logging
import re
from datetime import datetime, UTC
from typing import Optional, List, Dict, Any, Union
from .review_provider import ReviewProvider
from .github_client import GitHubClient
from .llm_client import RateLimitError

logger = logging.getLogger(__name__)


class SpecUpdater:
    """Automated spec.md project progress documentation."""

    def __init__(self, github_client: GitHubClient, review_provider: ReviewProvider):
        """Initialize spec updater.

        Args:
            github_client: GitHub API client
            review_provider: Provider for analysis and updates
        """
        self.github = github_client
        self.provider = review_provider

    async def update_spec(self, commit_sha: str, branch: str = "main") -> Optional[Union[str, Dict[str, Any]]]:
        """Update spec.md with project progress documentation.

        Args:
            commit_sha: Commit SHA to document
            branch: Branch to update spec on

        Returns:
            str: Updated spec content on success
            Dict[str, Any]: Error dict with success=False, error_type, message on rate limit
            None: If update fails
        """
        logger.info(f"Generating spec.md update for commit {commit_sha}")

        # Fetch commit info
        commit_info = await self.github.get_commit_info(commit_sha)
        if not commit_info:
            logger.error("Failed to fetch commit info")
            return None

        # Fetch commit diff (Fix Issue 3)
        diff = await self.github.get_commit_diff(commit_sha)
        if not diff:
            logger.warning("Failed to fetch commit diff, proceeding with empty diff")
            diff = ""

        # Fetch current spec.md
        current_spec = await self.github.get_file_content("spec.md", ref=branch)
        if current_spec is None:
            logger.info("spec.md not found, creating new one")
            current_spec = self._create_initial_spec()

        # Generate spec update
        try:
            # Pass diff explicitly - provider now returns tuple (content, metadata)
            updated_spec, usage_metadata = await self.provider.update_spec(commit_info, diff, current_spec)
            # Store metadata for later logging
            self._last_usage_metadata = usage_metadata
        except RateLimitError as e:
            logger.error("Spec update failed: LLM rate-limited (429)")
            return {
                "success": False,
                "error_type": "llm_rate_limited",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Failed to generate spec update: {e}")
            return None

        if not updated_spec:
            logger.error("Failed to generate spec update")
            return None

        # Clean up entry (Fix Issue 4)
        updated_spec = self._clean_spec_entry(updated_spec)

        # Append to spec
        updated_spec = self._append_to_spec(current_spec, updated_spec)
        logger.info("spec.md update generated")
        return updated_spec

    def _create_initial_spec(self) -> str:
        """Create initial spec.md structure.

        Returns:
            Initial spec.md content
        """
        return f"""# Project Specification & Progress

**Last Updated:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}

## Overview

This document tracks the project's development progress, architectural decisions, and milestones.

## Development Log

<!-- Automated entries will be appended below -->

"""

    def _append_to_spec(self, current_spec: str, entry: str) -> str:
        """Append new entry to spec.md.

        Args:
            current_spec: Current spec content
            entry: New entry to append

        Returns:
            Updated spec content
        """
        # Update the "Last Updated" timestamp
        updated_timestamp = datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')

        # Use regex to replace the existing timestamp line, supporting both bold and italic
        pattern = r'(\*\*|\*)Last Updated:(\*\*|\*).*'
        replacement = f"**Last Updated:** {updated_timestamp}"

        current_spec = re.sub(pattern, replacement, current_spec)

        # Append the new entry
        return current_spec + "\n\n" + entry

    def _clean_spec_entry(self, entry: str) -> str:
        """Clean up LLM output to extract pure spec entry.

        Args:
            entry: Raw LLM output

        Returns:
            Cleaned spec entry
        """
        # Remove markdown code block wrappers if present
        entry = re.sub(r'^```markdown\s*\n', '', entry, flags=re.MULTILINE)
        entry = re.sub(r'^```\s*\n', '', entry, flags=re.MULTILINE)
        entry = re.sub(r'\n```\s*$', '', entry, flags=re.MULTILINE)
        
        # Remove any leading/trailing whitespace
        entry = entry.strip()
        
        return entry