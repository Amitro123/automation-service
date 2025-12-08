# Project

Project description.

### 5. 🎯 PR-Centric Automation
- **Trigger Modes**: Configure to respond to PRs only, pushes only, or both
- **Trivial Change Filter**: Skip automation for small doc edits, whitespace-only changes
- **Smart Task Routing**: Code review only runs on code changes, not doc-only PRs
- **PR Review Comments**: Code reviews posted as PR reviews instead of commit comments
- **Configurable Thresholds**: Set max lines for trivial detection, doc file patterns

### 6. 🛡️ Robust Error Handling & Zero Silent Failures
- **No Silent Failures**: Every error is logged, tracked, and visible in SessionMemory
- **Comprehensive Logging**: `[CODE_REVIEW]`, `[ORCHESTRATOR]`, `[JULES]`, `[GROUPED_PR]` prefixes for easy debugging
- **Structured Error Returns**: All failures include `error_type` and `message` fields

### Review Provider Configuration
```bash
# Choose review provider: "llm" or "jules"
REVIEW_PROVIDER=llm
```bash
pip install -r requirements.txt
cp .env.example .env
Edit `.env` with your credentials.

### Review Provider Configuration
```bash
# Choose review provider: "llm" or "jules"
REVIEW_PROVIDER=llm
```bash
pip install -r requirements.txt
cp .env.example .env
Edit `.env` with your credentials.

automation_agent/
│   └── automation_agent/
│       ├── webhook_server.py          # Flask webhook endpoint
│       ├── orchestrator.py            # Coordinates 4 parallel tasks
│       ├── session_memory.py          # Session Memory Store
│       ├── code_reviewer.py           # LLM-powered code analysis
│       ├── code_review_updater.py     # Persistent review logging
│       ├── readme_updater.py          # Smart README updates
│       ├── github_client.py           # GitHub API wrapper
│       ├── llm_client.py              # OpenAI/Anthropic/Gemini abstraction
│       └── main.py                    # Entry point
├── dashboard/                         # React + Vite dashboard
│   ├── App.tsx                        # Main dashboard UI
│   ├── components/                    # UI components
│   ├── services/
│   ├── App.css
│   └── vite.config.ts
Dashboard runs on: **http://localhost:5173**
- 🗺️ Interactive architecture diagrams (Live from `ARCHITECTURE.md`)
- 📜 Session History & Run Logs

See [`dashboard/DASHBOARD_SETUP.md`](dashboard/DASHBOARD_SETUP.md) for detailed setup and API integration instructions.

**Using CI results in dashboard:**
1. Download `mutation_results.json` from workflow artifacts
2. Place in `dashboard/public/` folder
3. Restart dashboard
4. Dashboard displays real mutation score

See [`.github/workflows/MUTATION_TESTING.md`](.github/workflows/MUTATION_TESTING.md) for details.
On Windows, the feature will show as "skipped" with instructions. Run mutation tests in CI for best results.

## 🌐 Deployment

```mermaid
graph TD
    subgraph GitHub
        A[GitHub Repository]:::component
    end

    subgraph Server
        B[Webhook Server]:::component
        C[Orchestrator]:::orchestrator
        D[Session Memory Store]:::memory
    end

    subgraph Dashboard
        E[Dashboard]:::component
    end

    A -->|Push/PR| B
    B -->|Event| C
    C -->|Store Logs| D
    E -->|Fetch Metrics/History| B
    B -.->|Read| D

    %% Parallel Tasks
    subgraph Tasks["Parallel Tasks"]
        F[Code Reviewer]:::component
        G[README Updater]:::component
    end

    C -->|Code Review| F
    C -->|README Update| G
    F -->|Review Comments| A
    G -->|Update README| A

    classDef component fill:#f9f,stroke:#333,stroke-width:2px
    classDef orchestrator fill:#ccf,stroke:#333,stroke-width:2px
    classDef memory fill:#cff,stroke:#333,stroke-width:2px
## 📄 License
MIT

We maintain high code quality standards through multiple layers of testing and enforcement.

### Security (Bandit)
We use [Bandit](https://github.com/PyCQA/bandit) to scan for common security issues in Python code.
- **Run Locally**: `bandit -r src/ -ll`
- **CI**: Runs on every PR (blocking).