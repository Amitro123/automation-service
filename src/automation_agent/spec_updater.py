"""Automated spec.md project documentation module."""

import logging
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from .llm_client import LLMClient
from .github_client import GitHubClient

logger = logging.getLogger(__name__)


class SpecUpdater:
    """Automated spec.md project progress documentation."""

    def __init__(self, github_client: GitHubClient, llm_client: LLMClient):
        """Initialize spec updater.

        Args:
            github_client: GitHub API client
            llm_client: LLM client for analysis
        """
        self.github = github_client
        self.llm = llm_client

    async def update_spec(self, commit_sha: str, branch: str = "main") -> Optional[str]:
        """Update spec.md with project progress documentation.

        Args:
            commit_sha: Commit SHA to document
            branch: Branch to update spec on

        Returns:
            Updated spec content, or None if update fails
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
            # Pass diff explicitly
            updated_spec = await self.llm.update_spec(commit_info, diff, current_spec)
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

**Last Updated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

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
        updated_timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

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