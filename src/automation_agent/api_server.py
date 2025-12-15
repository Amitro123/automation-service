"""FastAPI server for GitHub Automation Agent with Dashboard API."""

import logging
import hmac
import hashlib
import asyncio
import re
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
from .memory import AcontextClient, SessionInsight

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
    mutationStatus: str = "unknown"  # skipped, success, failed, unknown
    mutationReason: Optional[str] = None


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


class AutomationTaskStatus(BaseModel):
    name: str
    status: str  # success, failed, skipped, pending
    details: Optional[str] = None


class PRItem(BaseModel):
    id: int
    title: str
    author: str
    status: str
    checksPassed: bool
    url: str
    createdAt: str
    automationStatus: List[AutomationTaskStatus] = []
    runId: Optional[str] = None


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
    projectProgress: float  # 0-100 percentage


class RepositoryStatus(BaseModel):
    name: str
    hasReadme: bool
    hasSpec: bool
    branch: str
    isSecure: bool
    lastPush: Optional[str] = None
    openIssues: int
    openPRs: int


# Acontext Context Suggest Models
class ContextSuggestRequest(BaseModel):
    """Request model for /api/context/suggest endpoint."""
    pr_title: str
    pr_files: List[str] = []
    limit: int = 5


class SessionInsightResponse(BaseModel):
    """Response model for a single session insight."""
    session_id: str
    pr_title: str
    timestamp: str
    status: str
    key_lessons: List[str]
    error_types: List[str]
    files_changed: List[str]
    similarity_score: float


class ContextSuggestResponse(BaseModel):
    """Response model for /api/context/suggest endpoint."""
    insights: List[SessionInsightResponse]
    total_sessions: int
    lessons_formatted: str


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
        gemini_max_rpm=config.GEMINI_MAX_RPM,
        gemini_min_delay=config.GEMINI_MIN_DELAY_SECONDS,
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
        try:
            import defusedxml.ElementTree as ET
        except ImportError:
            # Fallback to standard library if defusedxml not available
            import xml.etree.ElementTree as ET  # nosec B405
        import os
        
        # Get mutation score from mutation results if available
        mutation_score = 0.0
        mutation_status = "unknown"
        mutation_reason = None
        
        mutation_results = mutation_service.get_latest_results()
        if mutation_results:
            mutation_score = mutation_results.get("mutation_score", 0.0)
            mutation_status = mutation_results.get("status", "unknown")
            mutation_reason = mutation_results.get("reason")
        
        if not os.path.exists(file_path):
            # Return metrics with 0 coverage but potentially valid mutation score
            return CoverageMetrics(
                total=0.0,
                uncoveredLines=0,
                mutationScore=mutation_score,
                mutationStatus=mutation_status,
                mutationReason=mutation_reason
            )
            
        try:
            tree = ET.parse(file_path)  # nosec B314 - Using defusedxml when available
            root = tree.getroot()
            
            # Extract metrics
            line_rate = float(root.get("line-rate", 0))
            lines_valid = int(root.get("lines-valid", 0))
            lines_covered = int(root.get("lines-covered", 0))
            
            return CoverageMetrics(
                total=round(line_rate * 100, 1),
                uncoveredLines=lines_valid - lines_covered,
                mutationScore=mutation_score,
                mutationStatus=mutation_status,
                mutationReason=mutation_reason
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
        """Fetch real pull requests from GitHub and enrich with automation status."""
        try:
            prs = await github_client.list_pull_requests(state="open")
            pr_items = []
            
            # Get recent runs to match with PRs
            recent_runs = session_memory.get_history(limit=20)
            
            for pr in prs:
                # Check if PR has passing checks (simplified - just check if mergeable)
                checks_passed = pr.get("mergeable", False) or pr.get("mergeable_state") == "clean"
                
                # Match PR to automation run based on branch
                pr_branch = pr["head"]["ref"]
                matched_run = next((run for run in recent_runs if run.get("branch") == pr_branch), None)
                
                automation_status = []
                run_id = None
                
                if matched_run:
                    run_id = matched_run.get("id")
                    tasks = matched_run.get("tasks", {})
                    
                    # Map tasks to AutomationTaskStatus
                    if "code_review" in tasks:
                        automation_status.append(AutomationTaskStatus(
                            name="Code Review",
                            status=tasks["code_review"].get("status", "pending"),
                            details="Review generated" if tasks["code_review"].get("status") == "success" else None
                        ))
                    
                    if "readme_update" in tasks:
                        automation_status.append(AutomationTaskStatus(
                            name="README Update",
                            status=tasks["readme_update"].get("status", "pending"),
                            details="PR created" if tasks["readme_update"].get("status") == "success" else "No changes"
                        ))
                        
                    if "spec_update" in tasks:
                        automation_status.append(AutomationTaskStatus(
                            name="Spec Update",
                            status=tasks["spec_update"].get("status", "pending"),
                            details="Spec updated" if tasks["spec_update"].get("status") == "success" else "No changes"
                        ))
                
                pr_items.append(PRItem(
                    id=pr["number"],
                    title=pr["title"],
                    author=pr["user"]["login"],
                    status=pr["state"],
                    checksPassed=checks_passed,
                    url=pr["html_url"],
                    createdAt=pr["created_at"],
                    automationStatus=automation_status,
                    runId=run_id
                ))
            return pr_items
        except Exception as e:
            logger.error(f"Failed to fetch PRs: {e}")
            return []

    async def _calculate_progress() -> float:
        """Calculate project progress based on spec.md tasks."""
        try:
            content = await github_client.get_file_content("spec.md")
            if not content:
                return 0.0
            
            # Simple heuristic: Count [x] vs [ ]
            total_tasks = content.count("- [ ]") + content.count("- [x]")
            completed_tasks = content.count("- [x]")
            
            if total_tasks == 0:
                return 0.0
                
            return round((completed_tasks / total_tasks) * 100, 1)
        except Exception as e:
            logger.error(f"Failed to calculate progress: {e}")
            return 0.0

    @app.get("/api/metrics", response_model=DashboardMetrics)
    async def get_metrics():
        # 1. Get Coverage
        coverage = _parse_coverage()
        if not coverage:
            # Fallback mock
            coverage = CoverageMetrics(
                total=0.0, 
                uncoveredLines=0, 
                mutationScore=0.0,
                mutationStatus="unknown"
            )
            
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
        
        # 6. Calculate Project Progress
        project_progress = await _calculate_progress()
        
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
            ),
            projectProgress=project_progress
        )
    
    @app.get("/api/logs")
    async def get_logs(limit: int = 50):
        logs = list(app_state.logs)
        return logs[-limit:]

    @app.get("/api/history")
    async def get_history(limit: int = 50):
        return session_memory.get_history(limit)

    @app.get("/api/history/skipped")
    async def get_skipped_runs(limit: int = 20):
        """Get runs that were skipped due to trivial changes."""
        return session_memory.get_skipped_runs(limit)

    @app.get("/api/history/pr/{pr_number}")
    async def get_runs_by_pr(pr_number: int, limit: int = 10):
        """Get automation runs associated with a specific PR."""
        return session_memory.get_runs_by_pr(pr_number, limit)

    @app.get("/api/trigger-config")
    async def get_trigger_config():
        """Get current trigger configuration for dashboard display."""
        return {
            "trigger_mode": config.TRIGGER_MODE,
            "enable_pr_trigger": config.ENABLE_PR_TRIGGER,
            "enable_push_trigger": config.ENABLE_PUSH_TRIGGER,
            "trivial_filter_enabled": config.TRIVIAL_CHANGE_FILTER_ENABLED,
            "trivial_max_lines": config.TRIVIAL_MAX_LINES,
            "trivial_doc_paths": config.TRIVIAL_DOC_PATHS,
            "group_automation_updates": config.GROUP_AUTOMATION_UPDATES,
            "post_review_on_pr": config.POST_REVIEW_ON_PR,
        }
    
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
    
    @app.get("/api/spec")
    async def get_spec_content():
        """Get the content of spec.md."""
        try:
            content = await github_client.get_file_content("spec.md")
            if not content:
                raise HTTPException(status_code=404, detail="spec.md not found")
            return {"content": content}
        except Exception as e:
            logger.error(f"Failed to fetch spec.md: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # Acontext client for context suggestions
    acontext_client = AcontextClient(
        api_url=config.ACONTEXT_API_URL,
        storage_path=config.ACONTEXT_STORAGE_PATH,
        enabled=config.ACONTEXT_ENABLED,
        max_lessons=config.ACONTEXT_MAX_LESSONS,
    )

    @app.post("/api/context/suggest", response_model=ContextSuggestResponse)
    async def suggest_context(request: ContextSuggestRequest):
        """
        Get relevant insights from long-term memory based on PR details.
        
        For use by MCP or external integrations to retrieve learned lessons
        before starting automation runs.
        """
        try:
            # Query similar sessions
            insights = await acontext_client.query_similar_sessions(
                pr_title=request.pr_title,
                pr_files=request.pr_files,
                limit=request.limit,
            )
            
            # Format lessons for prompt injection
            lessons_formatted = acontext_client.format_lessons_for_prompt(insights)
            
            # Convert to response model
            insight_responses = [
                SessionInsightResponse(
                    session_id=i.session_id,
                    pr_title=i.pr_title,
                    timestamp=i.timestamp,
                    status=i.status,
                    key_lessons=i.key_lessons,
                    error_types=i.error_types,
                    files_changed=i.files_changed,
                    similarity_score=i.similarity_score,
                )
                for i in insights
            ]
            
            # Get total session count
            stats = acontext_client.get_stats()
            
            return ContextSuggestResponse(
                insights=insight_responses,
                total_sessions=stats.get("total_sessions", 0),
                lessons_formatted=lessons_formatted,
            )
        except Exception as e:
            logger.error(f"Failed to get context suggestions: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/context/stats")
    async def get_context_stats():
        """Get statistics about the long-term memory."""
        return acontext_client.get_stats()

    @app.post("/webhook")
    async def webhook(request: Request, background_tasks: BackgroundTasks):
        # Log incoming webhook request immediately
        delivery_id = request.headers.get("X-GitHub-Delivery", "unknown")
        event_type = request.headers.get("X-GitHub-Event", "unknown")
        logger.info(f"[WEBHOOK] Received webhook: event={event_type}, delivery={delivery_id}")
        app_state.add_log("INFO", f"Webhook received: {event_type} (delivery: {delivery_id[:8]}...)")
        
        # Verify signature
        signature = request.headers.get("X-Hub-Signature-256")
        if not signature:
            logger.warning(f"[WEBHOOK] Missing signature for delivery {delivery_id}")
            app_state.add_log("WARN", "Webhook rejected: missing signature")
            raise HTTPException(status_code=403, detail="Missing signature")
        
        body = await request.body()
        
        try:
            sha_name, sig = signature.split("=")
            if sha_name != "sha256":
                logger.warning(f"[WEBHOOK] Invalid algorithm: {sha_name}")
                raise HTTPException(status_code=403, detail="Invalid algorithm")
        except ValueError:
            logger.warning("[WEBHOOK] Invalid signature format")
            raise HTTPException(status_code=403, detail="Invalid signature format")
        
        mac = hmac.new(
            config.GITHUB_WEBHOOK_SECRET.encode(),
            msg=body,
            digestmod=hashlib.sha256
        )
        if not hmac.compare_digest(mac.hexdigest(), sig):
            logger.warning("[WEBHOOK] Invalid signature - HMAC mismatch")
            app_state.add_log("WARN", "Webhook rejected: invalid signature")
            raise HTTPException(status_code=403, detail="Invalid signature")
        
        logger.info("[WEBHOOK] Signature verified successfully")
        
        # Parse payload
        payload = await request.json()
        
        # Handle both push and pull_request events
        if event_type == "push":
            ref = payload.get('ref', 'N/A')
            commit_sha = payload.get('head_commit', {}).get('id', 'N/A')[:7]
            commit_msg = payload.get('head_commit', {}).get('message', 'N/A')[:50]
            logger.info(f"[WEBHOOK] Push event: ref={ref}, sha={commit_sha}, msg={commit_msg}")
            app_state.add_log("INFO", f"Push event: {ref} ({commit_sha}) - {commit_msg}")
            background_tasks.add_task(handle_event, orchestrator, event_type, payload)
            return {"message": "Automation started", "status": "accepted"}
        
        elif event_type == "pull_request":
            action = payload.get("action", "")
            pr_number = payload.get("number", "N/A")
            pr_data = payload.get("pull_request", {})
            pr_title = pr_data.get("title", "N/A")[:50]
            head_sha = pr_data.get("head", {}).get("sha", "N/A")[:7]
            head_ref = pr_data.get("head", {}).get("ref", "N/A")
            base_ref = pr_data.get("base", {}).get("ref", "N/A")
            
            logger.info(
                f"[WEBHOOK] PR event: action={action}, pr=#{pr_number}, "
                f"title='{pr_title}', head={head_ref}@{head_sha}, base={base_ref}"
            )
            
            # Only process opened, synchronize, reopened actions
            if action in ("opened", "synchronize", "reopened"):
                app_state.add_log(
                    "INFO", 
                    f"PR #{pr_number} ({action}): {head_ref}@{head_sha} -> {base_ref}"
                )
                logger.info(f"[WEBHOOK] Starting automation for PR #{pr_number} ({action})")
                background_tasks.add_task(handle_event, orchestrator, event_type, payload)
                return {"message": "Automation started", "status": "accepted"}
            else:
                logger.info(f"[WEBHOOK] Ignoring PR action: {action}")
                app_state.add_log("INFO", f"PR #{pr_number} action '{action}' ignored")
                return {"message": f"PR action '{action}' ignored", "status": "ok"}
        
        else:
            logger.info(f"[WEBHOOK] Ignoring event type: {event_type}")
            return {"message": f"Event '{event_type}' ignored", "status": "ok"}
    
    return app


async def handle_push_event(orchestrator: AutomationOrchestrator, payload: dict):
    """Handle push event in background (legacy method)."""
    await handle_event(orchestrator, "push", payload)


async def handle_event(orchestrator: AutomationOrchestrator, event_type: str, payload: dict):
    """Handle GitHub event in background using context-aware orchestration.
    
    Args:
        orchestrator: The automation orchestrator
        event_type: GitHub event type (push, pull_request)
        payload: Webhook payload
    """
    try:
        logger.info(f"[HANDLER] Starting handle_event for {event_type}")
        
        # For push events, check if there are commits
        if event_type == "push":
            commits = payload.get("commits", [])
            if not commits:
                logger.info("[HANDLER] No commits in push event, skipping")
                app_state.add_log("INFO", "No commits in push event")
                return
            logger.info(f"[HANDLER] Push has {len(commits)} commit(s)")
        
        # For PR events, log details and skip automation PRs
        if event_type == "pull_request":
            pr_number = payload.get("number")
            action = payload.get("action")
            pr_data = payload.get("pull_request", {})
            head_ref = pr_data.get("head", {}).get("ref", "")
            
            # Skip automation PRs to prevent infinite loops
            if head_ref.startswith("automation/"):
                logger.info(f"[HANDLER] Skipping automation PR #{pr_number} (branch: {head_ref})")
                app_state.add_log("INFO", f"Skipped automation PR #{pr_number}")
                return
            
            logger.info(f"[HANDLER] Processing PR #{pr_number} action={action}")
        
        app_state.add_log("INFO", f"Starting automation for {event_type} event...")
        
        # Use the new context-aware orchestration
        logger.info(f"[HANDLER] Calling run_automation_with_context...")
        result = await orchestrator.run_automation_with_context(event_type, payload)
        logger.info(f"[HANDLER] run_automation_with_context returned: success={result.get('success')}, skipped={result.get('skipped')}")
        
        # Log result based on run type
        if result.get("skipped"):
            skip_reason = result.get("skip_reason", "Unknown reason")
            run_type = result.get("run_type", "unknown")
            logger.info(f"[HANDLER] Run skipped: type={run_type}, reason={skip_reason}")
            app_state.add_log("INFO", f"Run skipped ({run_type}): {skip_reason}")
        elif result.get("success"):
            run_type = result.get("run_type", "full_automation")
            pr_number = result.get("pr_number")
            run_id = result.get("run_id", "unknown")
            logger.info(f"[HANDLER] Automation completed: type={run_type}, pr={pr_number}, run_id={run_id}")
            if pr_number:
                app_state.add_log("INFO", f"Automation completed ({run_type}) for PR #{pr_number}")
            else:
                app_state.add_log("INFO", f"Automation completed ({run_type})")
        else:
            logger.warning(f"[HANDLER] Automation completed with issues: {result}")
            app_state.add_log("WARN", "Automation completed with issues")
            
    except Exception as e:
        logger.error(f"[HANDLER] Event handling failed: {e}", exc_info=True)
        app_state.add_log("ERROR", f"Automation failed: {str(e)}")
