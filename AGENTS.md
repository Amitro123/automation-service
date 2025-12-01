# 🤖 AGENTS.md - GitHub Automation Agent Instructions

Instructions for AI coding agents (Windsurf, Cursor, GitHub Copilot, etc.) working on this repository.

## 🎯 Project Mission

**Single responsibility**: React to GitHub push events → run 3 parallel LLM-powered tasks:
1. **Code Review** → post intelligent feedback (comments/issues)
2. **README Update** → detect changes → create PR with docs
3. **Spec Update** → append structured progress log

**Success metric**: After every push → repo has fresh review + updated docs + progress log.

## 📁 Project Structure

src/automation_agent/ # Core package
├── __init__.py
├── main.py # Flask entry point (python -m automation_agent.main)
├── main_api.py # FastAPI entry point (NEW)
├── api_server.py # FastAPI server with Dashboard API (NEW)
├── webhook_server.py # Flask webhook endpoint
├── orchestrator.py # Coordinates 4 parallel tasks
├── session_memory.py # Session Memory Store (NEW)
├── code_reviewer.py # LLM-powered code analysis
├── code_review_updater.py # Persistent review logging
├── readme_updater.py # Smart README updates from diffs
├── spec_updater.py # Progress documentation
├── github_client.py # GitHub API wrapper
├── llm_client.py # OpenAI/Anthropic/Gemini abstraction
├── config.py # .env loading + validation
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

GitHub Push Event → webhook_server.py

Verify HMAC signature → extract diff/commit SHA

orchestrator.py → run 3 tasks IN PARALLEL:
↳ code_reviewer.py → post comment/issue
↳ readme_updater.py → create PR (if changes)
↳ spec_updater.py → append to spec.md

Log results + GitHub artifacts created
**All tasks log execution to `session_memory.py`**

## 📋 Agent Task Priorities

When working on this repo, focus on these **in order**:

### 1. **Core Flow Reliability** (Highest priority)
✅ Make webhook → orchestrator → GitHub side-effects robust
✅ Add retry logic for transient API failures
✅ Make tasks idempotent (handle webhook retries)
✅ Improve error handling + logging


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
5. 🚀 E2E Testing with ngrok
6. 🚀 Deployment readiness (Phase 4) - Docker + CI/CD

## 🚫 DON'T TOUCH (Unless Requested)

❌ Don't change webhook payload format
❌ Don't remove parallel task execution
❌ Don't hardcode config values
❌ Don't use print() for logging
❌ Don't make real API calls in tests


## 📈 Success Metrics for Agents

Your changes are successful if:
✅ pytest passes 100%
✅ Local webhook server starts cleanly
✅ Test push → 3 tasks complete → GitHub artifacts created
✅ Logs are structured + no secrets exposed
✅ README/spec.md stay accurate after changes

### 4. CodeReviewUpdater
- **Purpose**: Maintains a persistent log of all code reviews in `code_review.md`.
- **Logic**:
  - Runs after `CodeReviewer` completes successfully.
  - Summarizes the full review into a concise entry (Score, Key Issues, Action Items).
  - Appends to `code_review.md`.
- **Rules**:
  - Never overwrite the log, always append.
  - If `code_review.md` is missing, create it.
  - Use `LLMClient.summarize_review` for consistency.
