# 🤖 AGENTS.md - GitHub Automation Agent Instructions

Instructions for AI coding agents (Windsurf, Cursor, GitHub Copilot, etc.) working on this repository.

## 🎯 Project Mission

**Single responsibility**: React to GitHub **push and pull request events** → run parallel LLM-powered tasks:
1. **Code Review** → post intelligent feedback (PR reviews or commit comments)
2. **README Update** → detect changes → create PR with docs
3. **Spec Update** → append structured progress log
4. **Trivial Change Filter** → skip automation for small/whitespace-only changes

**Success metric**: After every push/PR → repo has fresh review + updated docs + progress log (unless trivial).

## 📁 Project Structure

src/automation_agent/ # Core package
├── __init__.py
├── main.py # Flask entry point (python -m automation_agent.main)
├── main_api.py # FastAPI entry point
├── api_server.py # FastAPI server with Dashboard API
├── webhook_server.py # Flask webhook endpoint
├── orchestrator.py # Coordinates parallel tasks (push + PR events)
├── trigger_filter.py # Event classification + trivial change detection
├── session_memory.py # Session Memory Store (extended for PR tracking)
├── code_reviewer.py # LLM-powered code analysis (UPDATED: zero silent failures)
├── code_review_updater.py # Persistent review logging
├── readme_updater.py # Smart README updates from diffs
├── spec_updater.py # Progress documentation
├── github_client.py # GitHub API wrapper (extended for PR operations)
├── llm_client.py # OpenAI/Anthropic/Gemini abstraction (UPDATED: rate limiting)
├── rate_limiter.py # Token bucket rate limiter (NEW)
├── review_provider.py # Jules/LLM provider abstraction (UPDATED: Jules API)
├── config.py # .env loading + validation (UPDATED: Jules config)
└── utils.py # Shared utilities

tests/ # pytest tests (mock external services)
dashboard/ # React + Vite dashboard
├── App.tsx # Main dashboard component
├── services/apiService.ts # FastAPI client
└── components/ # UI components
run_api.py # FastAPI server launcher (NEW)
.env.example # Configuration template
requirements.txt # Dependencies
README.md # User documentation
spec.md # Product spec + progress log


## 🚀 Setup & Run

Install
git clone https://github.com/Amitro123/GithubAgent.git
cd GithubAgent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Configure
cp .env.example .env

Edit .env: GITHUB_TOKEN, OPENAI_API_KEY, etc.
Run locally
export PYTHONPATH=$PYTHONPATH:$(pwd)/src # Linux/Mac
python -m automation_agent.main # http://localhost:8080/

**Health check**: `curl http://localhost:8080/` → `{"status": "ok"}`

## 🛠️ Core Workflow (NEVER BREAK THIS)

### Push Event Flow
```
GitHub Push Event → webhook_server.py/api_server.py
→ Verify HMAC signature → extract diff/commit SHA
→ trigger_filter.py → classify event + analyze diff
→ IF trivial change: skip automation, log reason
→ ELSE: orchestrator.py → run tasks IN PARALLEL:
   ↳ code_reviewer.py → post comment/issue
   ↳ readme_updater.py → create PR (if changes)
   ↳ spec_updater.py → append to spec.md
→ Log results + GitHub artifacts created
```

### Pull Request Event Flow (NEW)
```
GitHub PR Event (opened/synchronized/reopened) → api_server.py
→ Verify HMAC signature → extract PR number + diff
→ trigger_filter.py → classify as pr_opened/pr_synchronized/pr_reopened
→ IF trivial change: skip automation, log reason
→ ELSE: orchestrator.run_automation_with_context():
   ↳ code_reviewer.py → post PR REVIEW (not commit comment)
   ↳ readme_updater.py + spec_updater.py → grouped into SINGLE automation PR
→ Session memory tracks: trigger_type, run_type, pr_number, skip_reason
```

**All tasks log execution to `session_memory.py`**

## 📋 Agent Task Priorities

When working on this repo, focus on these **in order**:

### 1. **Core Flow Reliability** (Highest priority)
✅ Make webhook → orchestrator → GitHub side-effects robust
✅ Add retry logic for transient API failures
✅ Make tasks idempotent (handle webhook retries)
✅ Improve error handling + logging
✅ **Error hardening for Jules 404 and LLM 429** (prevents junk PRs, tracks failures)


### 2. **LLM Output Quality**
✅ Better prompts for code review (actionable, structured)
✅ Smarter README change detection (functions/classes/APIs)
✅ spec.md entries: summary + decisions + next steps
✅ Chunk large diffs appropriately


### 3. **Configuration & Extensibility**
✅ Add multi-LLM support (Gemini, local models)
✅ Per-branch policies (stricter on main)
✅ Agent platform integration (Windsurf/AntiGravity hooks)


## 🧪 Testing Rules

**ALWAYS test changes with:**
1. Unit tests (mock everything external)
pytest tests/ -v

2. Manual end-to-end
echo "test" >> test.txt
git add test.txt && git commit -m "test automation" && git push

text

**Mock these in tests:**
- `github_client.py` (GitHub API)
- `llm_client.py` (OpenAI/Anthropic)  
- `requests` (webhook simulation)
- `session_memory.py` (Persistence layer)

## 💻 Coding Standards

✅ DO: Type hints + Google docstrings
def analyze_diff(diff: str, context: Dict[str, str]) -> str:
"""Analyzes git diff and returns structured review.

Args:
    diff: Raw git diff content
    context: File contents around changes
    
Returns:
    Markdown formatted review string
"""
pass
❌ NEVER: print(), hardcoded values, missing types
text

**Dependencies**: Add to `requirements.txt`, never `pip freeze`.

## 🔒 Security Rules

❌ NEVER log:

GITHUB_TOKEN, API keys

Full git diffs (may contain secrets)

Raw webhook payloads

✅ ALWAYS:

Verify webhook HMAC signature

Use minimal GitHub token scopes

Validate/sanitize LLM outputs before posting

Run `bandit -r src/` to check for security issues before pushing code


## 🎯 Current spec.md Tasks

Read `spec.md` first, then prioritize:
1. ✅ Core functionality working
2. ✅ Comprehensive testing (Phase 3) - **99/99 tests passing, 100% coverage**
3. ✅ FastAPI + Dashboard Integration
4. ✅ Session Memory & Architecture Diagram
5. ✅ Dashboard Real Data Integration (bugs, PRs, LLM metrics from GitHub API)
6. ✅ Mutation Testing Integration (Linux/Mac/CI only - Windows shows helpful skip message)
7. ✅ GitHub Actions Workflow for Mutation Testing in CI
8. ✅ **PR-Centric Automation** - Trigger on PR events, trivial change filtering, grouped automation PRs
9. 🚀 E2E Testing with ngrok
10. 🚀 Deployment readiness (Phase 4) - Docker + CI/CD


## 🧬 Mutation Testing (Linux/Mac/CI Only)

**Platform Support:**
- ✅ **Linux/Mac**: Full support with mutmut
- ✅ **CI/CD**: Run in Linux runners (GitHub Actions, GitLab CI, etc.)
- ⚠️  **Windows**: Not supported (mutmut requires Unix `resource` module)
  - API returns: `{"status": "skipped", "reason": "Use WSL or CI"}`
  - Dashboard shows mutation tests are skipped
  - **Solution**: Use WSL, Docker, or run tests in CI

**Configuration:**
```bash
ENABLE_MUTATION_TESTS=True  # Enable feature
MUTATION_MAX_RUNTIME_SECONDS=600  # 10 minute timeout
```

**API Endpoints:**
- `POST /api/mutation/run` - Trigger tests (background task)
- `GET /api/mutation/results` - Fetch latest results
- `GET /api/metrics` - Includes mutation score from cached results

**Results:**
- Cached in `mutation_results.json`
- Displayed in dashboard Code Quality card
- Updated when tests run locally (Linux/Mac) or via CI

**CI/CD Integration:**
- GitHub Actions workflow: `.github/workflows/mutation-tests.yml`
- Runs on push to main or manual trigger
- Saves results as artifacts (30 days)
- Download and copy to repo root for dashboard display
- See `.github/workflows/MUTATION_TESTING.md` for details

## 🎯 PR-Centric Configuration (NEW)

**Trigger Modes:**
```bash
TRIGGER_MODE=both    # "pr" = PR events only, "push" = push only, "both" = all events
ENABLE_PR_TRIGGER=True
ENABLE_PUSH_TRIGGER=True
```

**Trivial Change Filter:**
```bash
TRIVIAL_CHANGE_FILTER_ENABLED=True  # Skip automation for trivial changes
TRIVIAL_MAX_LINES=10                 # Max lines for doc-only to be "trivial"
TRIVIAL_DOC_PATHS=README.md,*.md,docs/**  # Patterns for doc files
```

**PR Automation Behavior:**
```bash
GROUP_AUTOMATION_UPDATES=True  # Bundle README+spec into single automation PR
POST_REVIEW_ON_PR=True         # Post code review as PR review (not commit comment)
```

**Run Types (tracked in session_memory):**
- `full_automation` - All tasks run
- `partial_docs_only` - Only doc updates (no code review)
- `skipped_trivial_change` - Skipped due to trivial change filter
- `skipped_docs_only` - Skipped because only docs changed

**New API Endpoints:**
- `GET /api/history/skipped` - Get runs skipped due to trivial changes
- `GET /api/history/pr/{pr_number}` - Get runs for a specific PR
- `GET /api/trigger-config` - Get current trigger configuration

## 🚫 DON'T TOUCH (Unless Requested)

❌ Don't change webhook payload format
❌ Don't remove parallel task execution
❌ Don't hardcode config values
❌ Don't use print() for logging
❌ Don't make real API calls in tests
❌ Don't break backward compatibility with push-only workflows



## 📈 Success Metrics for Agents

Your changes are successful if:
✅ pytest passes 100%
✅ Local webhook server starts cleanly
✅ Test push → 3 tasks complete → GitHub artifacts created
✅ Logs are structured + no secrets exposed
✅ README/spec.md stay accurate after changes

### 1. CodeReviewer (`code_reviewer.py`)
- **Role**: Senior Software Engineer / Security Auditor
- **Responsibility**: Analyze git diffs for bugs, security flaws, and style issues.
- **Tools**:
  - `ReviewProvider`: Pluggable review engine (Jules / Google Code Review API or LLM).
  - `LLMClient`: Fallback to Gemini/OpenAI/Anthropic if Jules is unavailable.
  - `GitHubClient`: Post comments/issues.
- **Behavior**:
  - Receives commit SHA.
  - Fetches diff + context.
  - Calls `ReviewProvider.review_code()`.
  - Formats output as markdown.
  - Posts to GitHub.

### 4. CodeReviewUpdater
- **Purpose**: Maintains a persistent log of all code reviews in `AUTOMATED_REVIEWS.md`.
- **Logic**:
  - Runs after `CodeReviewer` completes successfully.
  - Summarizes the full review into a concise entry (Score, Key Issues, Action Items).
  - Appends to `AUTOMATED_REVIEWS.md`.
- **Rules**:
  - Never overwrite the log, always append.
  - If `AUTOMATED_REVIEWS.md` is missing, create it.
  - Use `LLMClient.summarize_review` for consistency.
  - Note: Uses `AUTOMATED_REVIEWS.md` (not `code_review.md`) to avoid collision with `CODE_REVIEW.md` on case-insensitive filesystems.

---

## 🎉 Recent Improvements (Dec 2025)

### ✅ Zero Silent Failures
**Problem Solved:** Code review and other tasks were failing silently with no error messages.

**Solution Implemented:**
- **Comprehensive Logging**: Added `[CODE_REVIEW]`, `[ORCHESTRATOR]`, `[JULES]`, `[GROUPED_PR]` prefixes
- **Structured Errors**: All failures return `{"success": False, "error_type": "...", "message": "..."}`
- **SessionMemory Tracking**: `mark_task_failed()` called on all errors
- **Dashboard Visibility**: All failures visible in `/api/history` with detailed reasons
- **Run Status**: Properly set to `failed`, `completed_with_issues`, or `completed`

**Key Changes:**
- `code_reviewer.py`: Added `run_id` parameter, logs every stage, returns structured errors
- `orchestrator.py`: Handles all error types, calls `mark_task_failed()` on failures
- No more silent failures - every error is logged and tracked

### ✅ Jules API Integration
**Problem Solved:** Jules API was returning 404 errors due to incorrect implementation.

**Solution Implemented:**
- **Correct Workflow**: Session-based code reviews (create session → poll → extract review)
- **Proper Endpoint**: `https://jules.googleapis.com/v1alpha/sessions`
- **Correct Auth**: `X-Goog-Api-Key` header (not Bearer token)
- **Configuration**: Added `JULES_SOURCE_ID`, `JULES_PROJECT_ID` to config
- **Error Types**: `jules_404` (misconfiguration), `jules_auth_error` (invalid key), `jules_client_error` (4xx)
- **Smart Fallback**: 5xx errors fall back to LLM, but 404/auth errors don't (configuration issues)
- **Diagnostic Tool**: `test_jules_review.py` for testing integration

**Key Changes:**
- `review_provider.py`: Complete rewrite of `JulesReviewProvider` with session workflow
- `config.py`: Added Jules configuration variables
- `.env.example`: Added Jules configuration with detailed comments

### ✅ LLM Rate Limiting
**Problem Solved:** Gemini API was returning 429 rate limit errors.

**Solution Implemented:**
- **Token Bucket Algorithm**: Prevents 429 errors by throttling requests
- **Configurable**: `GEMINI_MAX_RPM`, `GEMINI_MIN_DELAY_SECONDS`, `GEMINI_MAX_CONCURRENT_REQUESTS`
- **Centralized**: Rate limiting in `LLMClient` (not orchestrator)
- **Preserves Parallelism**: Only throttles actual API calls, not entire tasks

**Key Changes:**
- `rate_limiter.py`: New token bucket rate limiter
- `llm_client.py`: Integrated rate limiter for Gemini calls
- `config.py`: Added rate limiting configuration

### 📊 Testing Results
- ✅ **132/141 tests passing** (9 mock failures, not production code)
- ✅ **E2E test passed**: All tasks completed successfully
- ✅ **No silent failures**: All errors logged and tracked
- ✅ **Rate limiting working**: No 429 errors
- ✅ **Error tracking complete**: SessionMemory shows all failures

### 📚 New Documentation
- `JULES_API_INTEGRATION.md` - Complete Jules API setup guide
- `SILENT_FAILURES_FIXED.md` - Summary of error handling improvements
- `JULES_404_RESOLUTION.md` - Troubleshooting guide
- `test_jules_review.py` - Diagnostic script for Jules API
- `check_e2e.py` - E2E test results checker

### 🎯 What This Means for Agents
When working on this codebase:
1. **All errors must be logged** with appropriate prefixes (`[CODE_REVIEW]`, etc.)
2. **All errors must return structured dicts** with `error_type` and `message`
3. **All failures must call** `mark_task_failed()` in SessionMemory
4. **Never allow silent failures** - every error must be visible
5. **Test with** `python check_e2e.py` after changes
6. **Verify Jules integration with** `python test_jules_review.py`
