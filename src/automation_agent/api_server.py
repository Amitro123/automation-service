"""FastAPI server for GitHub Automation Agent with Dashboard API."""

import logging
import hmac
import hashlib
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from collections import deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .config import Config
from .github_client import GitHubClient
from .llm_client import LLMClient
from .code_reviewer import CodeReviewer
from .readme_updater import ReadmeUpdater
from .spec_updater import SpecUpdater
from .code_review_updater import CodeReviewUpdater
from .orchestrator import AutomationOrchestrator
from .session_memory import SessionMemoryStore
from . import mutation_service

logger = logging.getLogger(__name__)


# ============== Pydantic Models ==============

class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str


class CoverageMetrics(BaseModel):
    total: float
    uncoveredLines: int
    mutationScore: float


class LLMMetrics(BaseModel):
    tokensUsed: int
    estimatedCost: float
    efficiencyScore: float
    sessionMemoryUsage: float


class TaskItem(BaseModel):
    id: str
    title: str
    status: str


class BugItem(BaseModel):
    id: str
    title: str
    severity: str
    status: str
    createdAt: str


class PRItem(BaseModel):
    id: int
    title: str
    author: str
    status: str
    checksPassed: bool


class SecurityStatus(BaseModel):
    isSecure: bool
    vulnerabilities: int
    lastScan: str


class DashboardMetrics(BaseModel):
    coverage: CoverageMetrics
    llm: LLMMetrics
    tasks: List[TaskItem]
    bugs: List[BugItem]
    prs: List[PRItem]
    logs: List[LogEntry]
    security: SecurityStatus


class RepositoryStatus(BaseModel):
    name: str
    hasReadme: bool
    hasSpec: bool
    branch: str
    isSecure: bool
    lastPush: Optional[str] = None
    openIssues: int
    openPRs: int


# ============== Application State ==============

class AppState:
    """Application state for tracking ephemeral logs."""
    
    def __init__(self):
        self.logs: deque = deque(maxlen=100)
        self.start_time: datetime = datetime.now(timezone.utc)
        
    def add_log(self, level: str, message: str):
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).strftime("%H:%M:%S"),
            level=level,
            message=message
        )
        self.logs.append(entry)


# Global state instance
app_state = AppState()
session_memory = SessionMemoryStore()


def create_api_server(config: Config) -> FastAPI:
    """Create FastAPI application with all routes."""
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app_state.add_log("INFO", "GitHub Automation Agent API started")
        yield
        app_state.add_log("INFO", "Server shutting down")
    
    app = FastAPI(
        title="GitHub Automation Agent API",
        description="API for GitHub Automation Agent with Dashboard",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # CORS for dashboard
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize components
    github_client = GitHubClient(
        token=config.GITHUB_TOKEN,
        owner=config.REPOSITORY_OWNER,
        repo=config.REPOSITORY_NAME,
    )
    
    # Select appropriate API key based on provider
    api_key = None
    if config.LLM_PROVIDER == "openai":
        api_key = config.OPENAI_API_KEY
    elif config.LLM_PROVIDER == "anthropic":
        api_key = config.ANTHROPIC_API_KEY
    elif config.LLM_PROVIDER == "gemini":
        api_key = config.GEMINI_API_KEY
    
    llm_client = LLMClient(
        provider=config.LLM_PROVIDER,
        model=config.LLM_MODEL,
        api_key=api_key,
    )
    
    # Initialize Review Provider
    from .review_provider import LLMReviewProvider, JulesReviewProvider
    
    # Default to LLM provider
    review_provider = LLMReviewProvider(llm_client)
    
    # If Jules is configured, wrap the LLM provider as fallback
    if config.REVIEW_PROVIDER == "jules":
        review_provider = JulesReviewProvider(config, fallback_provider=review_provider)
        app_state.add_log("INFO", "Using Jules Review Provider")
    else:
        app_state.add_log("INFO", f"Using LLM Review Provider ({config.LLM_PROVIDER})")
    
    code_reviewer = CodeReviewer(github_client, review_provider)
    readme_updater = ReadmeUpdater(github_client, review_provider)
    spec_updater = SpecUpdater(github_client, review_provider)
    code_review_updater = CodeReviewUpdater(github_client, llm_client) # Keep using LLM for summary generation
    
    orchestrator = AutomationOrchestrator(
        github_client=github_client,
        code_reviewer=code_reviewer,
        readme_updater=readme_updater,
        spec_updater=spec_updater,
        code_review_updater=code_review_updater,
        session_memory=session_memory,
        config=config,
    )
    
    # Store in app state
    app.state.config = config
    app.state.github_client = github_client
    app.state.orchestrator = orchestrator
    
    # ============== Routes ==============
    
    @app.get("/")
    async def health_check():
        uptime = datetime.now(timezone.utc) - app_state.start_time
        return {
            "status": "healthy",
            "service": "GitHub Automation Agent",
            "version": "1.0.0",
            "uptime": str(uptime).split('.')[0]
        }
    
    def _parse_coverage(file_path: str = "coverage.xml") -> Optional[CoverageMetrics]:
        """Parse coverage.xml to extract metrics."""
        import xml.etree.ElementTree as ET
        import os
        
        if not os.path.exists(file_path):
            return None
            
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract metrics
            line_rate = float(root.get("line-rate", 0))
            lines_valid = int(root.get("lines-valid", 0))
            lines_covered = int(root.get("lines-covered", 0))
            
            # Get mutation score from mutation results if available
            mutation_score = 0.0
            mutation_results = mutation_service.get_latest_results()
            if mutation_results:
                mutation_score = mutation_results.get("mutation_score", 0.0)
            
            return CoverageMetrics(
                total=round(line_rate * 100, 1),
                uncoveredLines=lines_valid - lines_covered,
                mutationScore=mutation_score
            )
        except Exception as e:
            logger.error(f"Failed to parse coverage.xml: {e}")
            return None
    
    async def _fetch_bugs() -> List[BugItem]:
        """Fetch real bugs from GitHub issues."""
        try:
            issues = await github_client.list_issues(state="open", labels=["bug"])
            bugs = []
            for issue in issues:
                bugs.append(BugItem(
                    id=str(issue["number"]),
                    title=issue["title"],
                    severity="medium",  # GitHub doesn't have severity, could parse from labels
                    status="open",
                    createdAt=issue["created_at"]
                ))
            return bugs
        except Exception as e:
            logger.error(f"Failed to fetch bugs: {e}")
            return []
    
    async def _fetch_prs() -> List[PRItem]:
        """Fetch real pull requests from GitHub."""
        try:
            prs = await github_client.list_pull_requests(state="open")
            pr_items = []
            for pr in prs:
                # Check if PR has passing checks (simplified - just check if mergeable)
                checks_passed = pr.get("mergeable", False) or pr.get("mergeable_state") == "clean"
                
                pr_items.append(PRItem(
                    id=pr["number"],
                    title=pr["title"],
                    author=pr["user"]["login"],
                    status=pr["state"],
                    checksPassed=checks_passed
                ))
            return pr_items
        except Exception as e:
            logger.error(f"Failed to fetch PRs: {e}")
            return []

    @app.get("/api/metrics", response_model=DashboardMetrics)
    async def get_metrics():
        # 1. Get Coverage
        coverage = _parse_coverage()
        if not coverage:
            # Fallback mock
            coverage = CoverageMetrics(total=0.0, uncoveredLines=0, mutationScore=0.0)
            
        # 2. Get Global Metrics (LLM)
        global_metrics = session_memory.get_global_metrics()
        
        # 3. Get Tasks from latest run
        tasks = []
        history = session_memory.get_history(limit=1)
        if history:
            latest_run = history[0]
            # Map run tasks to TaskItem
            # Assuming run["tasks"] structure: {"code_review": {...}, "readme_update": {...}}
            run_tasks = latest_run.get("tasks", {})
            
            # Helper to map status
            def map_status(status: str) -> str:
                if status == "success": return "Completed"
                if status == "running": return "InProgress"
                if status == "failed": return "Failed"
                return "Pending"

            tasks = [
                TaskItem(id="t1", title="Code Review", status=map_status(run_tasks.get("code_review", {}).get("status", "pending"))),
                TaskItem(id="t2", title="README Update", status=map_status(run_tasks.get("readme_update", {}).get("status", "pending"))),
                TaskItem(id="t3", title="Spec Update", status=map_status(run_tasks.get("spec_update", {}).get("status", "pending"))),
            ]
        else:
            # Fallback if no history
            tasks = [
                TaskItem(id="t1", title="Code Review", status="Pending"),
                TaskItem(id="t2", title="README Update", status="Pending"),
                TaskItem(id="t3", title="Spec Update", status="Pending"),
            ]
        
        # 4. Fetch real bugs and PRs
        bugs = await _fetch_bugs()
        prs = await _fetch_prs()
        
        # 5. Calculate real LLM metrics
        history_count = len(session_memory.get_history(limit=1000))  # Get all history
        session_memory_usage = round((history_count / 1000) * 100, 1)  # Percentage of max capacity
        
        # Calculate efficiency score based on success rate
        efficiency_score = 88.0  # Default
        if history:
            successful_runs = sum(1 for run in session_memory.get_history(limit=10) 
                                 if run.get("status") == "success")
            efficiency_score = round((successful_runs / min(10, history_count)) * 100, 1) if history_count > 0 else 0.0
        
        return DashboardMetrics(
            coverage=coverage,
            llm=LLMMetrics(
                tokensUsed=global_metrics.get("total_tokens", 0),
                estimatedCost=global_metrics.get("total_cost", 0.0),
                efficiencyScore=efficiency_score,
                sessionMemoryUsage=session_memory_usage
            ),
            tasks=tasks,
            bugs=bugs,
            prs=prs,
            logs=list(app_state.logs),
            security=SecurityStatus(
                isSecure=True,
                vulnerabilities=0,
                lastScan=datetime.now(timezone.utc).isoformat()
            )
        )
    
    @app.get("/api/logs")
    async def get_logs(limit: int = 50):
        logs = list(app_state.logs)
        return logs[-limit:]

    @app.get("/api/history")
    async def get_history(limit: int = 50):
        return session_memory.get_history(limit)
    
    @app.post("/api/mutation/run")
    async def run_mutation_tests_endpoint(background_tasks: BackgroundTasks):
        """Trigger mutation tests to run in the background."""
        if not Config.ENABLE_MUTATION_TESTS:
            raise HTTPException(
                status_code=400,
                detail="Mutation testing is disabled. Set ENABLE_MUTATION_TESTS=True in .env to enable."
            )
        
        # Run mutation tests in background
        def run_tests():
            try:
                logger.info("Starting mutation tests in background...")
                results = mutation_service.run_mutation_tests(
                    max_runtime_seconds=Config.MUTATION_MAX_RUNTIME_SECONDS
                )
                
                # Check if tests were skipped (e.g., on Windows)
                if results.get("status") == "skipped":
                    logger.warning(f"Mutation tests skipped: {results.get('reason')}")
                else:
                    logger.info(f"Mutation tests completed: {results.get('mutation_score', 0)}%")
            except Exception as e:
                logger.error(f"Error running mutation tests: {e}")
        
        background_tasks.add_task(run_tests)
        
        return {
            "status": "started",
            "message": "Mutation tests are running in the background. Check /api/mutation/results for progress."
        }
    
    @app.get("/api/mutation/results")
    async def get_mutation_results():
        """Get the latest mutation test results."""
        results = mutation_service.get_latest_results()
        
        if results is None:
            raise HTTPException(
                status_code=404,
                detail="No mutation test results available. Run POST /api/mutation/run first."
            )
        
        return results
    
    @app.get("/api/repository/{repo_name}/status", response_model=RepositoryStatus)
    async def get_repository_status(repo_name: str):
        has_readme = await github_client.get_file_content("README.md") is not None
        has_spec = await github_client.get_file_content("spec.md") is not None
        
        return RepositoryStatus(
            name=repo_name,
            hasReadme=has_readme,
            hasSpec=has_spec,
            branch="master",
            isSecure=True,
            openIssues=0,
            openPRs=0
        )

    @app.get("/api/architecture")
    async def get_architecture():
        """Get the current architecture diagram."""
        try:
            with open(config.ARCHITECTURE_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                # Extract mermaid block
                import re
                match = re.search(r"```mermaid\n(.*?)\n```", content, re.DOTALL)
                if match:
                    return {"diagram": match.group(1)}
                return {"diagram": "graph TD\nError[Could not parse diagram]"}
        except (FileNotFoundError, IOError, OSError):
            logger.exception("Failed to read architecture file")
            return {"diagram": "graph TD\nError[Failed to read architecture file]"}
    
    @app.post("/webhook")
    async def webhook(request: Request, background_tasks: BackgroundTasks):
        # Verify signature
        signature = request.headers.get("X-Hub-Signature-256")
        if not signature:
            raise HTTPException(status_code=403, detail="Missing signature")
        
        body = await request.body()
        
        try:
            sha_name, sig = signature.split("=")
            if sha_name != "sha256":
                raise HTTPException(status_code=403, detail="Invalid algorithm")
        except ValueError:
            raise HTTPException(status_code=403, detail="Invalid signature format")
        
        mac = hmac.new(
            config.GITHUB_WEBHOOK_SECRET.encode(),
            msg=body,
            digestmod=hashlib.sha256
        )
        if not hmac.compare_digest(mac.hexdigest(), sig):
            raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Check event type
        event_type = request.headers.get("X-GitHub-Event")
        if event_type != "push":
            return {"message": "Event ignored", "status": "ok"}
        
        payload = await request.json()
        app_state.add_log("INFO", f"Received push event: {payload.get('head_commit', {}).get('message', 'N/A')[:50]}")
        
        # Process in background
        background_tasks.add_task(handle_push_event, orchestrator, payload)
        
        return {"message": "Automation started", "status": "accepted"}
    
    return app


async def handle_push_event(orchestrator: AutomationOrchestrator, payload: dict):
    """Handle push event in background."""
    try:
        commits = payload.get("commits", [])
        if not commits:
            app_state.add_log("INFO", "No commits in push event")
            return
        
        app_state.add_log("INFO", "Starting automation tasks...")
        result = await orchestrator.run_automation(payload)
        
        if result.get("success"):
            app_state.add_log("INFO", "Automation completed successfully")
        else:
            app_state.add_log("WARN", f"Automation completed with issues")
            
    except Exception as e:
        app_state.add_log("ERROR", f"Automation failed: {str(e)}")
        logger.error(f"Push event handling failed: {e}", exc_info=True)
