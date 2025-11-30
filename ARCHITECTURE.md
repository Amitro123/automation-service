# System Architecture

This document describes the high-level architecture of the GitHub Automation Agent.

## Diagram

```mermaid
graph TD
    %% Styles
    classDef component fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef memory fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;
    classDef external fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef orchestrator fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;

    %% External Systems
    subgraph External[External Systems]
        GitHub[GitHub Push Event]:::external
        GitHubAPI[GitHub API]:::external
        LLM["LLM (Gemini/OpenAI/Anthropic)"]:::external
    end

    %% Core System
    subgraph System[Automation Agent]
        Webhook[Webhook Server]:::component
        Orchestrator[Async Orchestrator]:::orchestrator
        
        %% Parallel Tasks
        subgraph Tasks[Parallel Tasks]
            Reviewer[Code Reviewer]:::component
            ReadmeUp[README Updater]:::component
            SpecUp[Spec Updater]:::component
            ReviewUp[Code Review Updater]:::component
        end
    end

    %% Session Memory / Persistent Storage
    subgraph Memory[Session Memory / Artifacts]
        SpecMD[spec.md]:::memory
        ReadmeMD[README.md]:::memory
        ReviewMD[code_review.md]:::memory
    end

    %% Dashboard
    subgraph Frontend[Frontend]
        Dashboard[React Dashboard]:::component
    end

    %% Data Flow
    GitHub -->|POST /webhook| Webhook
    Webhook -->|Trigger| Orchestrator
    Orchestrator -->|Parallel Exec| Reviewer
    Orchestrator -->|Parallel Exec| ReadmeUp
    Orchestrator -->|Parallel Exec| SpecUp
    Orchestrator -->|Parallel Exec| ReviewUp

    %% Dashboard Interactions
    Dashboard -->|Fetch Metrics| Webhook
    Dashboard -->|View Logs| Webhook

    %% Component Interactions
    Reviewer -->|Analyze Diff| LLM
    Reviewer -->|Post Comment| GitHubAPI

    ReadmeUp -->|Read Content| ReadmeMD
    ReadmeUp -->|Generate Update| LLM
    ReadmeUp -->|Create PR| GitHubAPI

    SpecUp -->|Read History| SpecMD
    SpecUp -->|Generate Entry| LLM
    SpecUp -->|Append Entry| GitHubAPI

    ReviewUp -->|Read Log| ReviewMD
    ReviewUp -->|Summarize| LLM
    ReviewUp -->|Append Log| GitHubAPI

    %% Memory Updates
    SpecUp -.->|Update| SpecMD
    ReadmeUp -.->|Update| ReadmeMD
    ReviewUp -.->|Update| ReviewMD
```

## Live Updates

To ensure this diagram stays in sync with the codebase, use the `generate_architecture_diagram.py` script.

### Manual Generation
Run the script to output the current Mermaid syntax:
```bash
python generate_architecture_diagram.py
```

### CI/CD Integration (Recommended)
You can add a GitHub Actions workflow to verify that the diagram in `ARCHITECTURE.md` matches the script output.

**Example Step:**
```yaml
- name: Verify Architecture Diagram
  run: |
    python generate_architecture_diagram.py > current_diagram.mmd
    # Compare with existing diagram or fail if out of sync
```

### Best Practices
1.  **Single Source of Truth**: Treat the code as the truth. The diagram is a view of the code.
2.  **Automate**: Use pre-commit hooks or CI jobs to regenerate the diagram when core files change.
3.  **Review**: Include architecture changes in code reviews.
