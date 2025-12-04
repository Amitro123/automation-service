# 🤖 GitHub Automation Agent

An autonomous GitHub automation system that triggers on **push and pull request events** to perform intelligent code review, automatic README and code_review.md updates, and project progress documentation. Features **PR-centric orchestration** with trivial change filtering to optimize LLM token usage.

## 💡 Why This Agent?

- **Reduces repetitive code review work** — highlights risky changes and suggests fixes automatically
- **Keeps docs always fresh** — README, spec.md, and code_review.md stay in sync with actual code changes
- **Intelligent layer over GitHub** — uses advanced LLMs + async orchestration instead of rigid YAML workflows

## ✨ Features

### 1. 🔍 Automated Code Review
- **Intelligent Analysis**: Uses LLMs (GPT-4o / Claude 3.5 / Gemini Pro) to analyze code changes
- **Comprehensive Feedback**: Code quality, bugs, security, performance, best practices
- **Flexible Output**: Commit comments, PR comments, GitHub issues, and persistent code_review.md logging
- **Structured Reviews**: Strengths, issues, suggestions, security concerns
- **Session Memory**: Maintains historic context for continuous improvement

### 2. 📝 Automatic Documentation Updates
- **README Updater**: Context-aware, analyzes diffs to update docs
- **Spec Updater**: Dynamically appends development progress logs
- **Code Review Updater**: Appends review summaries to persistent logs

### 3. 📊 Real-Time Dashboard
- **Live Metrics**: Real test coverage from coverage.xml, LLM usage tracking, token costs, calculated efficiency scores
- **Real Data Integration**: Fetches live bugs from GitHub issues, open PRs with check status, session memory metrics
- **Visual Progress**: Task tracking with real statuses from automation runs
- **Architecture Visualization**: Interactive Mermaid diagrams with clear component descriptions
- **System Logs**: Real-time log viewer with filtering
- **Security Status**: Bandit scan results and vulnerability tracking
- **Multi-Repository**: Switch between repositories with live updates

### 4. 📊 Project Progress & Metrics
- Visual progress tracking with real-time updates
- Test coverage and mutation testing integration using tools like mutmut
- LLM usage stats: token consumption, cost estimation, efficiency
- Security guardrails integrated with Bandit scans and CI/CD enforcement
- Multi-repository support with auto-detection of required files (README.md, spec.md)

### 5. 🎯 PR-Centric Automation (NEW)
- **Trigger Modes**: Configure to respond to PRs only, pushes only, or both
- **Trivial Change Filter**: Skip automation for small doc edits, whitespace-only changes
- **Smart Task Routing**: Code review only runs on code changes, not doc-only PRs
- **Grouped Automation PRs**: README + spec updates bundled into single PR per source PR
- **PR Review Comments**: Code reviews posted as PR reviews instead of commit comments
- **Configurable Thresholds**: Set max lines for trivial detection, doc file patterns

### 6. 🛡️ Robust Error Handling & Zero Silent Failures
- **No Silent Failures**: Every error is logged, tracked, and visible in SessionMemory
- **Comprehensive Logging**: `[CODE_REVIEW]`, `[ORCHESTRATOR]`, `[JULES]`, `[GROUPED_PR]` prefixes for easy debugging
- **Structured Error Returns**: All failures include `error_type` and `message` fields
- **Jules API Integration**: Proper session-based workflow with official API (https://jules.googleapis.com/v1alpha)
- **Jules Error Types**: `jules_404` (misconfiguration), `jules_auth_error` (invalid key), `jules_client_error` (4xx)
- **LLM Rate Limiting**: Token bucket algorithm prevents 429 errors (configurable RPM/delay)
- **Smart Fallback**: Jules 5xx errors fall back to LLM, but 404/auth errors don't (configuration issues)
- **SessionMemory Tracking**: `mark_task_failed()` called on all errors with error_type and message
- **Dashboard Visibility**: All failures visible in `/api/history` with detailed error reasons
- **Run Status**: Properly set to `failed`, `completed_with_issues`, or `completed` based on task results

### 7. 🔒 Security Features
- HMAC-SHA256 verification of webhook signatures
- Minimal GitHub token scopes
- No secrets logged; credential storage limited to environment variables
- Automated security scans integrated in CI

### 8. 🗺️ Dynamic Architecture Diagram
- ARCHITECTURE.md includes a live Mermaid diagram reflecting system components and project progress
- Automatically updated via scripts/CI when system or specs change
- **Visualized in the Dashboard**

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- GitHub Personal Access Token (repo + issues + pull_requests scope)
- OpenAI, Anthropic, or Gemini API key

### Installation
```bash
git clone https://github.com/Amitro123/GithubAgent.git
cd GithubAgent
git checkout automation-agent-setup

python -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
Edit `.env` with your credentials.

### Review Provider Configuration
```bash
# Choose review provider: "llm" or "jules"
REVIEW_PROVIDER=llm

# For LLM provider (Gemini/OpenAI/Anthropic)
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MAX_RPM=10              # Rate limiting
GEMINI_MIN_DELAY_SECONDS=2.0   # Min delay between calls

# For Jules API provider (optional)
JULES_API_KEY=your_jules_api_key_here
JULES_API_URL=https://jules.googleapis.com/v1alpha
JULES_SOURCE_ID=sources/github/owner/repo  # Get from: curl 'https://jules.googleapis.com/v1alpha/sources' -H 'X-Goog-Api-Key: YOUR_KEY'
**Test Jules Integration:**
```bash
python test_jules_review.py  # Validates config and tests API
### PR-Centric Configuration (Optional)
```bash
# Trigger mode: "pr", "push", or "both" (default: both)
TRIGGER_MODE=both

# Skip automation for trivial changes
TRIVIAL_CHANGE_FILTER_ENABLED=True
TRIVIAL_MAX_LINES=10

# Post code review on PR instead of commit
POST_REVIEW_ON_PR=True

# Group doc updates into single automation PR
GROUP_AUTOMATION_UPDATES=True
### Run Locally

#### Option 1: FastAPI Server (Recommended - includes Dashboard API)
```bash
# Windows (PowerShell)
.venv\Scripts\python.exe run_api.py

# Linux/Mac
python run_api.py
#### Option 2: Flask Server (Legacy webhook-only)
```bash
# Windows (PowerShell)
$env:PYTHONPATH = "$PWD/src"
python -m automation_agent.main

## 🧲 Agent Platform Integration (Optional)

Compatible with **Windsurf**, **AntiGravity**, **n8n**, or any agent orchestrator:

GitHub Push → Agent Platform Webhook → Orchestrator → GitHub API
**Example flow:**
1. Platform receives webhook → normalizes payload
2. Calls `code_reviewer.py` → posts review comment/issue
3. Calls `readme_updater.py` → creates documentation PR
4. Calls `spec_updater.py` → appends progress entry
5. Calls `code_review_updater.py` → appends review summary to logs
6. Platform handles retries, logging, notifications

## 📋 Workflow

### Standard Flow (Push Events)
1. **Developer pushes code** → webhook triggers
2. **Webhook verifies signature** → extracts diff/commit data
3. **Trigger filter analyzes diff** → classifies as trivial/code/docs change
4. **Orchestrator runs tasks based on change type:**
   - Code review → comment/issue + persistent logs (code changes only)
   - README update → PR (if changes detected)
   - spec.md update → append entry
   - code_review.md update → append review summary with session memory
5. **Results posted** → repo stays documented automatically and progress tracked

### PR-Centric Flow (Pull Request Events)
1. **Developer opens/updates PR** → webhook triggers
2. **Trigger filter classifies event** → pr_opened, pr_synchronized, pr_reopened
3. **Diff analyzed for trivial changes** → skip automation if trivial
4. **Orchestrator runs context-aware tasks:**
   - Code review → posted as **PR review comment** (not commit comment)
   - Documentation updates → grouped into **single automation PR** per source PR
5. **Results linked to source PR** → clear audit trail

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8080/
### Test Full Flow
```bash
echo "# Test change" >> test.txt
git add test.txt
git commit -m "test: trigger automation"
git push
**Expected results:**
- ✅ Code review comment/issue
- ✅ README PR (if applicable)
- ✅ spec.md + code_review.md entries appended

### Test Status
**Current Pass Rate**: 100% (99/99 tests passing) as of 2025-11-30

- ✅ Unit Tests
- ✅ Integration Tests
- ✅ Edge Cases
- ✅ Load Tests

## 📦 Project Structure

automation_agent/
├── src/
│   └── automation_agent/
│       ├── webhook_server.py          # Flask webhook endpoint
│       ├── orchestrator.py            # Coordinates 4 parallel tasks
│       ├── session_memory.py          # Session Memory Store (NEW)
│       ├── code_reviewer.py           # LLM-powered code analysis
│       ├── code_review_updater.py     # Persistent review logging
│       ├── readme_updater.py          # Smart README updates
│       ├── spec_updater.py            # Progress documentation
│       ├── github_client.py           # GitHub API wrapper
│       ├── llm_client.py              # OpenAI/Anthropic/Gemini abstraction
│       └── main.py                    # Entry point
├── dashboard/                         # React + Vite dashboard (NEW)
│   ├── App.tsx                        # Main dashboard UI
│   ├── components/                    # UI components
│   ├── services/
│   │   └── apiService.ts              # Backend API client
│   └── DASHBOARD_SETUP.md             # Dashboard documentation
└── tests/                             # Pytest test suite
## 🗺️ Roadmap

- ✅ Multi-LLM support (Gemini, local models)
- 🔗 Multi-repo orchestration
- 🎛️ Per-branch policies (strict main, relaxed feature branches)
- 🔔 Integrations: Slack/Jira/n8n notifications
- 📊 Metrics dashboard for review quality and velocity

## 🔒 Security

- HMAC-SHA256 webhook signature verification
- Minimal GitHub token scopes
- No logging of secrets/diffs
- Environment-only credential storage
- Guardrails tests with Bandit integrated into CI (`.github/workflows/security.yml`)

## 📊 Dashboard

### Running the Dashboard

The project includes a real-time dashboard for monitoring automation metrics, test coverage, LLM usage, and system status.

**Start the dashboard:**
```bash
cd dashboard
npm install  # First time only
npm run dev
Dashboard runs on: **http://localhost:5173**

**Features:**
- 📊 Live test coverage and mutation scores
- 💰 LLM token usage and cost tracking
- 📋 Task progress and bug tracking
- 🔐 Security status from Bandit scans
- 📝 Real-time system logs
- 🗺️ Interactive architecture diagrams (Live from `ARCHITECTURE.md`)
- 📜 Session History & Run Logs

See [`dashboard/DASHBOARD_SETUP.md`](dashboard/DASHBOARD_SETUP.md)

5. Displays results in Actions summary
6. (Optional) Comments on PRs with scores

**Using CI results in dashboard:**
1. Download `mutation_results.json` from workflow artifacts
2. Copy to repo root
3. Restart API server: `python run_api.py`
4. Dashboard displays real mutation score

See [`.github/workflows/MUTATION_TESTING.md`](.github/workflows/MUTATION_TESTING.md) for details.
 On Windows, the feature will show as "skipped" with instructions. Run mutation tests in CI for best results.
 for detailed setup and API integration instructions.

## 🌐 Deployment

### Docker Deployment
```bash
docker build -t automation-agent .
docker run -p 8080:8080 --env-file .env automation-agent
### Docker Compose (Recommended)
```bash
docker-compose up -d
### CI/CD
Included GitHub Actions workflow (`.github/workflows/ci.yml`) runs tests on every push and builds Docker image on main branch pushes.

## Diagram

The project includes an ARCHITECTURE.md file with a live Mermaid diagram illustrating the system and project progress.

**Example Mermaid snippet:**

```mermaid
graph TD
    %% Backend Core (The Brain)
    subgraph Backend["Backend Core (The Brain)"]
        Webhook[Webhook Server]:::component
        Orchestrator[Async Orchestrator]:::orchestrator
        SessionMem[Session Memory Store]:::memory
        
        %% Parallel Tasks
        subgraph Tasks["Parallel Tasks"]
            Reviewer[Code Reviewer]:::component
            ReadmeUp[README Updater]:::component
            SpecUp[Spec Updater]:::component
            ReviewUp[Code Review Updater]:::component
        end
    end

    %% Frontend (Consumer)
    subgraph Frontend["Frontend (Consumer)"]
        Dashboard[React Dashboard]:::frontend
    end

    Webhook -->|Trigger| Orchestrator
    Orchestrator -->|Init Run| SessionMem
    Dashboard -->|Fetch Metrics/History| Webhook
    Webhook -.->|Read| SessionMem
The diagram updates automatically as the project evolves.

## 📄 License
MIT