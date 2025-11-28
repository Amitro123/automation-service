# 🤖 GitHub Automation Agent

An autonomous GitHub automation system that triggers on push events to perform intelligent code review, automatic README updates, and project progress documentation.

## 💡 Why This Agent?

- **Reduces repetitive code review work** - highlights risky changes and suggests fixes automatically  
- **Keeps docs always fresh** - README and spec.md stay in sync with actual code changes  
- **Intelligent layer over GitHub** - uses LLMs + orchestration instead of rigid YAML workflows  

## ✨ Features

### 1. 🔍 Automated Code Review
- **Intelligent Analysis**: Uses LLM (GPT-4o / Claude 3.5) to analyze code changes
- **Comprehensive Feedback**: Code quality, bugs, security, performance, best practices
- **Flexible Output**: Commit comments, PR comments, or GitHub issues
- **Structured Reviews**: Strengths, issues, suggestions, security concerns

### 2. 📝 Automatic README Updates
- **Smart Detection**: Identifies new functions, classes, APIs, dependencies
- **Context-Aware**: Analyzes git diffs to understand changes
- **Preserves Structure**: Maintains existing format/tone, touches only relevant sections
- **Safe Updates**: Creates PRs (configurable) instead of direct commits

### 3. 📊 Project Progress Documentation (spec.md)
- **Development Log**: Tracks evolution with structured entries per push
- **Comprehensive Entries**: Change summaries, architecture decisions, milestones
- **Historical Context**: Considers recent commits for insights
- **Next Steps**: Suggests remaining tasks automatically

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Push Event                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Webhook Server (Flask)                    │
│                                                              │
│  • Receives push events                                     │
│  • Verifies HMAC-SHA256 signature                          │
│  • Extracts commit information                              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Automation Orchestrator                    │
│                                                              │
│  Coordinates three parallel tasks:                          │
└───────────┬─────────────────┬────────────────┬──────────────┘
            │                 │                │
            ↓                 ↓                ↓
    ┌───────────┐     ┌──────────┐    ┌──────────┐
    │   Code    │     │ README   │    │  Spec    │
    │  Review   │     │ Updater  │    │ Updater  │
    └─────┬─────┘     └────┬─────┘    └────┬─────┘
          │                │               │
          ↓                ↓               ↓
    ┌─────────────────────────────────────────┐
    │          LLM Client (OpenAI/Anthropic)  │
    └─────────────────────────────────────────┘
          │                │               │
          ↓                ↓               ↓
    ┌──────────┐     ┌──────────┐    ┌──────────┐
    │ Post     │     │ Create   │    │ Append   │
    │ Comment  │     │ PR/Commit│    │ to spec  │
    └──────────┘     └──────────┘    └──────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- GitHub Personal Access Token (repo + issues + pull_requests scope)
- OpenAI API key or Anthropic API key

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
```

Edit `.env` with your credentials.

### Run Locally
```bash
# Ensure src is in PYTHONPATH
# Windows (PowerShell)
$env:PYTHONPATH = "$PWD/src"
# Linux/Mac
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

python -m automation_agent.main
```

Server runs on http://localhost:8080/

## ⚙️ Configuration

**.env file:**
```ini
# GitHub
GITHUB_TOKEN=ghp_your_token_here
GITHUB_WEBHOOK_SECRET=your_secret_here
REPOSITORY_OWNER=your_username
REPOSITORY_NAME=your_repo

# LLM
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your_key_here
LLM_MODEL=gpt-4o-mini

# Behavior
CREATE_PR=True
AUTO_COMMIT=False
POST_REVIEW_AS_ISSUE=False

# Optional: Agent Platforms
GRAVITY_ENABLED=False
GRAVITY_API_KEY=
GRAVITY_WORKFLOW_ID=
```

## 🧲 Agent Platform Integration (Optional)

Works with **Windsurf**, **Gravity**, **n8n**, or any agent orchestrator:

GitHub Push → Agent Platform Webhook → Orchestrator → GitHub API

**Example flow:**
1. Platform receives webhook → normalizes payload
2. Calls `code_reviewer.py` → posts review comment/issue  
3. Calls `readme_updater.py` → creates documentation PR
4. Calls `spec_updater.py` → appends progress entry
5. Platform handles retries, logging, notifications

## 📋 Workflow

1. **Developer pushes code** → webhook triggers
2. **Webhook verifies signature** → extracts diff/commit data  
3. **Orchestrator runs 3 parallel tasks:**
   - Code review → comment/issue
   - README update → PR (if changes detected)
   - spec.md update → append entry
4. **Results posted** → repo stays documented automatically

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8080/
```

### Test Full Flow
```bash
echo "# Test change" >> test.txt
git add test.txt
git commit -m "test: trigger automation"
git push
```

**Expected results:**
✅ Code review comment/issue  
✅ README PR (if applicable)  
✅ spec.md entry appended [web:35][memory:25]

## 📦 Project Structure

```
automation_agent/
├── src/
│   └── automation_agent/
│       ├── webhook_server.py # Flask webhook endpoint
│       ├── orchestrator.py # Coordinates 3 parallel tasks
│       ├── code_reviewer.py # LLM-powered code analysis
│       ├── readme_updater.py # Smart README updates
│       ├── spec_updater.py # Progress documentation
│       ├── github_client.py # GitHub API wrapper
│       ├── llm_client.py # OpenAI/Anthropic abstraction
│       └── main.py # Entry point
```

## 🗺️ Roadmap

- 🔄 Multi-LLM support (Gemini, local models)
- 🔗 Multi-repo orchestration  
- 🎛️ Per-branch policies (stricter main, relaxed feature branches)
- 🔔 Integrations: Slack/Jira/n8n notifications
- 📊 Metrics dashboard for review quality/velocity

## 🔒 Security

- HMAC-SHA256 webhook signature verification
- Minimal GitHub token scopes
- No logging of secrets/diffs
- Environment-only credential storage

## 🌐 Deployment

**Local dev:** `ngrok http 8080`  
**Production:** Docker, Railway, Render, or agent platforms

See [SETUP.md](SETUP.md)

## 📄 License
MIT