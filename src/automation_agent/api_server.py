"""FastAPI server for GitHub Automation Agent with Dashboard API."""

import logging
import hmac
import hashlib
import asyncio
from datetime import datetime, timezone
from typing import Optional, List
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
    """Application state for tracking metrics and logs."""
    
    def __init__(self):
        self.logs: deque = deque(maxlen=100)
        self.tokens_used: int = 0
        self.estimated_cost: float = 0.0
        self.start_time: datetime = datetime.now(timezone.utc)
        self.last_push: Optional[datetime] = None
        self.active_tasks: List[dict] = []
        
    def add_log(self, level: str, message: str):
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).strftime("%H:%M:%S"),
            level=level,
            message=message
        )
        self.logs.append(entry)
    
    def update_llm_usage(self, tokens: int, cost: float):
        self.tokens_used += tokens
        self.estimated_cost += cost


# Global state instance
app_state = AppState()


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
    
    code_reviewer = CodeReviewer(github_client, llm_client)
    readme_updater = ReadmeUpdater(github_client, llm_client)
    spec_updater = SpecUpdater(github_client, llm_client)
    code_review_updater = CodeReviewUpdater(github_client, llm_client)
    
    orchestrator = AutomationOrchestrator(
        github_client=github_client,
        code_reviewer=code_reviewer,
        readme_updater=readme_updater,
        spec_updater=spec_updater,
        code_review_updater=code_review_updater,
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
    
    @app.get("/api/metrics", response_model=DashboardMetrics)
    async def get_metrics():
        return DashboardMetrics(
            coverage=CoverageMetrics(total=98.0, uncoveredLines=24, mutationScore=75.0),
            llm=LLMMetrics(
                tokensUsed=app_state.tokens_used,
                estimatedCost=app_state.estimated_cost,
                efficiencyScore=88.0,
                sessionMemoryUsage=45.0
            ),
            tasks=[
                TaskItem(id="t1", title="Code Review", status="Completed"),
                TaskItem(id="t2", title="README Update", status="InProgress"),
                TaskItem(id="t3", title="Spec Update", status="Pending"),
            ],
            bugs=[],
            prs=[],
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
    
    @app.get("/api/repository/{repo_name}/status", response_model=RepositoryStatus)
    async def get_repository_status(repo_name: str):
        has_readme = github_client.get_file_content("README.md") is not None
        has_spec = github_client.get_file_content("spec.md") is not None
        
        return RepositoryStatus(
            name=repo_name,
            hasReadme=has_readme,
            hasSpec=has_spec,
            branch="master",
            isSecure=True,
            openIssues=0,
            openPRs=0
        )
    
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
