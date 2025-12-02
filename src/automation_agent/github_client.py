"""GitHub API client wrapper for automation operations."""

import logging
from typing import Optional, Dict, Any, List
import httpx

logger = logging.getLogger(__name__)


class GitHubClient:
    """GitHub API client with retry logic and error handling."""

    def __init__(self, token: str, owner: str, repo: str):
        """Initialize GitHub client.

        Args:
            token: GitHub personal access token
            owner: Repository owner
            repo: Repository name
        """
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Automation-Agent"
        }
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    async def _get_client(self) -> httpx.AsyncClient:
        """Create and return an httpx AsyncClient."""
        return httpx.AsyncClient(headers=self.headers, timeout=self.timeout)

    async def get_commit_diff(self, commit_sha: str) -> Optional[str]:
        """Get the diff for a specific commit.

        Args:
            commit_sha: Commit SHA to fetch diff for

        Returns:
            Diff content as string, or None if error
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/commits/{commit_sha}"
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.get(url, headers={**self.headers, "Accept": "application/vnd.github.v3.diff"})
                response.raise_for_status()
                return response.text
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch commit diff: {e}")
            return None

    async def get_commit_info(self, commit_sha: str) -> Optional[Dict[str, Any]]:
        """Get commit information.

        Args:
            commit_sha: Commit SHA

        Returns:
            Commit data dictionary or None
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/commits/{commit_sha}"
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch commit info: {e}")
            return None

    async def post_commit_comment(self, commit_sha: str, body: str) -> bool:
        """Post a comment on a commit.

        Args:
            commit_sha: Commit SHA to comment on
            body: Comment body text

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/commits/{commit_sha}/comments"
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.post(url, json={"body": body})
                response.raise_for_status()
                logger.info(f"Posted comment on commit {commit_sha}")
                return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to post commit comment: {e}")
            return False

    async def create_issue(self, title: str, body: str, labels: Optional[List[str]] = None) -> Optional[int]:
        """Create a GitHub issue.

        Args:
            title: Issue title
            body: Issue body
            labels: Optional list of label names

        Returns:
            Issue number if successful, None otherwise
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues"
        payload = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels

        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                issue_number = response.json()["number"]
                logger.info(f"Created issue #{issue_number}")
                return issue_number
        except httpx.HTTPError as e:
            logger.error(f"Failed to create issue: {e}")
            return None

    async def get_file_content(self, file_path: str, ref: str = "main") -> Optional[str]:
        """Get content of a file from the repository.

        Args:
            file_path: Path to file in repository
            ref: Git reference (branch, tag, or commit SHA)

        Returns:
            File content as string, or None if not found
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/contents/{file_path}"
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.get(url, params={"ref": ref})
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                import base64
                content = response.json()["content"]
                return base64.b64decode(content).decode("utf-8")
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch file content: {e}")
            return None

    async def update_file(self, file_path: str, content: str, message: str, branch: str = "main") -> bool:
        """Update or create a file in the repository.

        Args:
            file_path: Path to file in repository
            content: New file content
            message: Commit message
            branch: Branch to commit to

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/contents/{file_path}"
        import base64

        # Get current file SHA if it exists
        sha = None
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.get(url, params={"ref": branch})
                if response.status_code == 200:
                    sha = response.json()["sha"]
        except httpx.HTTPError:
            pass

        payload = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha

        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.put(url, json=payload)
                response.raise_for_status()
                logger.info(f"Updated file {file_path} on branch {branch}")
                return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to update file: {e}")
            return False

    async def create_branch(self, branch_name: str, from_branch: str = "main") -> bool:
        """Create a new branch.

        Args:
            branch_name: Name for the new branch
            from_branch: Source branch to branch from

        Returns:
            True if successful, False otherwise
        """
        # Get SHA of source branch
        ref_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/ref/heads/{from_branch}"
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.get(ref_url)
                response.raise_for_status()
                sha = response.json()["object"]["sha"]

                # Create new branch
                create_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/refs"
                payload = {"ref": f"refs/heads/{branch_name}", "sha": sha}
                response = await client.post(create_url, json=payload)
                response.raise_for_status()
                logger.info(f"Created branch {branch_name}")
                return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to create branch: {e}")
            return False

    async def create_pull_request(
        self, title: str, body: str, head: str, base: str = "main"
    ) -> Optional[int]:
        """Create a pull request.

        Args:
            title: PR title
            body: PR body
            head: Branch containing changes
            base: Branch to merge into

        Returns:
            PR number if successful, None otherwise
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/pulls"
        payload = {"title": title, "body": body, "head": head, "base": base}

        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                pr_number = response.json()["number"]
                logger.info(f"Created PR #{pr_number}")
                return pr_number
        except httpx.HTTPError as e:
            logger.error(f"Failed to create pull request: {e}")
            return None

    async def get_recent_commits(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent commits from the repository.

        Args:
            limit: Maximum number of commits to fetch

        Returns:
            List of commit dictionaries
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/commits"
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.get(url, params={"per_page": limit})
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch recent commits: {e}")
            return []
    async def list_issues(self, state: str = "open", labels: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """List issues from the repository.

        Args:
            state: Issue state filter ("open", "closed", or "all")
            labels: Optional list of label names to filter by

        Returns:
            List of issue dictionaries
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues"
        params = {"state": state, "per_page": 100}
        if labels:
            params["labels"] = ",".join(labels)

        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                # Filter out pull requests (GitHub API returns PRs as issues)
                issues = [issue for issue in response.json() if "pull_request" not in issue]
                return issues
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch issues: {e}")
            return []

    async def list_pull_requests(self, state: str = "open") -> List[Dict[str, Any]]:
        """List pull requests from the repository.

        Args:
            state: PR state filter ("open", "closed", or "all")

        Returns:
            List of pull request dictionaries
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/pulls"
        params = {"state": state, "per_page": 100}

        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch pull requests: {e}")
            return []

    async def get_pull_request(self, pr_number: int) -> Optional[Dict[str, Any]]:
        """Get a specific pull request.

        Args:
            pr_number: Pull request number

        Returns:
            Pull request data dictionary or None
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/pulls/{pr_number}"
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch pull request #{pr_number}: {e}")
            return None

    async def get_pull_request_diff(self, pr_number: int) -> Optional[str]:
        """Get the diff for a pull request.

        Args:
            pr_number: Pull request number

        Returns:
            Diff content as string, or None if error
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/pulls/{pr_number}"
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers={**self.headers, "Accept": "application/vnd.github.v3.diff"}
                )
                response.raise_for_status()
                return response.text
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch PR diff: {e}")
            return None

    async def post_pull_request_comment(self, pr_number: int, body: str) -> bool:
        """Post a comment on a pull request.

        Args:
            pr_number: Pull request number
            body: Comment body text

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues/{pr_number}/comments"
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.post(url, json={"body": body})
                response.raise_for_status()
                logger.info(f"Posted comment on PR #{pr_number}")
                return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to post PR comment: {e}")
            return False

    async def post_pull_request_review(
        self,
        pr_number: int,
        body: str,
        event: str = "COMMENT",
        commit_id: Optional[str] = None,
    ) -> bool:
        """Post a review on a pull request.

        Args:
            pr_number: Pull request number
            body: Review body text
            event: Review event type (APPROVE, REQUEST_CHANGES, COMMENT)
            commit_id: Optional commit SHA to review

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/pulls/{pr_number}/reviews"
        payload: Dict[str, Any] = {"body": body, "event": event}
        if commit_id:
            payload["commit_id"] = commit_id

        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                logger.info(f"Posted review on PR #{pr_number}")
                return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to post PR review: {e}")
            return False

    async def find_open_pr_for_branch(self, branch: str) -> Optional[Dict[str, Any]]:
        """Find an open PR for a given branch.

        Args:
            branch: Branch name to search for

        Returns:
            PR data if found, None otherwise
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/pulls"
        params = {"state": "open", "head": f"{self.owner}:{branch}"}

        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                prs = response.json()
                return prs[0] if prs else None
        except httpx.HTTPError as e:
            logger.error(f"Failed to find PR for branch {branch}: {e}")
            return None

    async def update_pull_request(
        self,
        pr_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
    ) -> bool:
        """Update a pull request's title or body.

        Args:
            pr_number: Pull request number
            title: New title (optional)
            body: New body (optional)

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/pulls/{pr_number}"
        payload: Dict[str, Any] = {}
        if title:
            payload["title"] = title
        if body:
            payload["body"] = body

        if not payload:
            return True  # Nothing to update

        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.patch(url, json=payload)
                response.raise_for_status()
                logger.info(f"Updated PR #{pr_number}")
                return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to update PR: {e}")
            return False

    async def add_files_to_branch(
        self,
        branch: str,
        files: Dict[str, str],
        message: str,
    ) -> bool:
        """Add or update multiple files on a branch in a single commit.

        Args:
            branch: Branch to commit to
            files: Dictionary of file_path -> content
            message: Commit message

        Returns:
            True if successful, False otherwise
        """
        # For simplicity, we'll update files one by one
        # A more efficient implementation would use the Git Data API
        for file_path, content in files.items():
            success = await self.update_file(
                file_path=file_path,
                content=content,
                message=message,
                branch=branch,
            )
            if not success:
                return False
        return True
