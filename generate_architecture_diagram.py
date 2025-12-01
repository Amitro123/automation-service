#!/usr/bin/env python3
"""
Script to generate a Mermaid architecture diagram for the GitHub Automation Agent.
This script updates ARCHITECTURE.md with the latest diagram and description.
"""

import os

def generate_mermaid() -> str:
    """Generate Mermaid architecture diagram for GitHub Automation Agent."""
    diagram = """graph TD
    %% Styles
    classDef component fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef memory fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;
    classDef external fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef orchestrator fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef frontend fill:#ffe0b2,stroke:#f57c00,stroke-width:2px;
    classDef primary fill:#d1c4e9,stroke:#512da8,stroke-width:3px;
    classDef fallback fill:#f5f5f5,stroke:#9e9e9e,stroke-width:2px,stroke-dasharray: 5,5;
    classDef ci fill:#e0f7fa,stroke:#006064,stroke-width:2px;
    classDef api fill:#ffecb3,stroke:#ff6f00,stroke-width:2px;

    %% External Systems
    subgraph External["External Systems"]
        GitHub[GitHub Push Event]:::external
        GitHubAPI[GitHub API]:::external
    end

    %% CI/Automation Layer
    subgraph CI["CI/Automation (Linux Runner)"]
        Pytest[pytest]:::ci
        Mutmut[mutmut]:::ci
    end

    %% Backend Core (The Brain)
    subgraph Backend["Backend Core (The Brain)"]
        Webhook[Webhook Server]:::component
        Orchestrator[Async Orchestrator]:::orchestrator
        SessionMem[Session Memory Store]:::memory
        MutationService[Mutation Service]:::component
        
        %% Review Providers Abstraction
        subgraph ReviewAbstraction["Review Providers"]
            ReviewProv[ReviewProvider Interface]:::component
        end

        %% Parallel Tasks
        subgraph Tasks["Parallel Tasks"]
            Reviewer[Code Reviewer]:::component
            ReadmeUp[README Updater]:::component
            SpecUp[Spec Updater]:::component
            ReviewUp[Code Review Updater]:::component
        end
    end

    %% API Gateway Layer
    subgraph APILayer["API Gateway Layer"]
        APIServer[FastAPI API Server]:::api
    end

    %% Artifacts
    subgraph Artifacts["Repo Artifacts"]
        SpecMD[spec.md]:::memory
        ReadmeMD[README.md]:::memory
        ReviewMD[code_review.md]:::memory
        MutationRes[mutation_results.json]:::memory
        CoverageXML[coverage.xml]:::memory
    end

    %% Frontend (Consumer)
    subgraph Frontend["Frontend (Consumer)"]
        Dashboard[React Dashboard]:::frontend
    end

    %% Review Providers Implementation
    subgraph Providers["Review Engines"]
        Jules["Jules API (Primary)"]:::primary
        LLM["LLMs (Gemini/OpenAI/Anthropic) Fallback"]:::fallback
    end

    %% Data Flow - Ingress
    GitHub -->|POST /webhook| Webhook
    Webhook -->|Trigger| Orchestrator
    
    %% Orchestration
    Orchestrator -->|Init Run| SessionMem
    Orchestrator -->|Parallel Exec| Reviewer
    Orchestrator -->|Parallel Exec| ReadmeUp
    Orchestrator -->|Parallel Exec| SpecUp
    Orchestrator -->|Parallel Exec| ReviewUp
    Orchestrator -->|Update Status| SessionMem

    %% Mutation & CI Flow
    Webhook -->|Run /api/mutation/run| MutationService
    MutationService -->|Exec| Mutmut
    Mutmut -->|Write| MutationRes
    Pytest -->|Write| CoverageXML
    
    %% Metrics Flow
    MutationRes -->|Read| APIServer
    CoverageXML -->|Read| APIServer
    SessionMem -->|Read Metrics| APIServer

    %% API Layer
    APIServer -->|/api/metrics| Dashboard
    APIServer -->|/api/architecture| Dashboard
    APIServer -->|/api/history| Dashboard
    APIServer -->|/api/mutation/results| Dashboard

    %% Component Interactions
    Reviewer -->|Delegate| ReviewProv
    ReadmeUp -->|Delegate| ReviewProv
    SpecUp -->|Delegate| ReviewProv
    
    %% Review Provider Logic
    ReviewProv -->|Primary Selection| Jules
    ReviewProv -.->|Fallback if Failed| LLM
    
    %% External Interactions
    Reviewer -->|Post Comment| GitHubAPI
    Reviewer -->|Log Result| SessionMem

    ReadmeUp -->|Read Content| ReadmeMD
    ReadmeUp -->|Create PR| GitHubAPI
    ReadmeUp -->|Log Result| SessionMem

    SpecUp -->|Read History| SpecMD
    SpecUp -->|Append Entry| GitHubAPI
    SpecUp -->|Log Result| SessionMem

    ReviewUp -->|Read Log| ReviewMD
    ReviewUp -->|Summarize| LLM
    ReviewUp -->|Append Log| GitHubAPI
    
    %% Memory Updates
    SpecUp -.->|Update| SpecMD
    ReadmeUp -.->|Update| ReadmeMD
    ReviewUp -.->|Update| ReviewMD

    %% Notes
    note1[Mutation testing supported only on<br/>Linux/Mac/CI. Skipped on Windows.]
    Mutmut --- note1
    
    note2[Review engine configurable via<br/>environment variables.]
    ReviewProv --- note2
    """
    return diagram

def update_architecture_file(output_path: str = "ARCHITECTURE.md"):
    """Update ARCHITECTURE.md with the generated diagram."""
    diagram = generate_mermaid()
    
    # Read existing file to preserve Recent Enhancements section
    recent_enhancements = ""
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            existing_content = f.read()
            # Extract everything after "## Recent Enhancements"
            if "## Recent Enhancements" in existing_content:
                parts = existing_content.split("## Recent Enhancements", 1)
                recent_enhancements = "\n---\n\n## Recent Enhancements" + parts[1]
    except FileNotFoundError:
        pass  # File doesn't exist yet, that's okay
    
    content = f"""# System Architecture

This document describes the high-level architecture of the GitHub Automation Agent.

## Overview

The system is designed with a **Backend Core** acting as the "brain" and a **Frontend Dashboard** acting as a consumer/observer.

- **Backend Core**: Handles webhooks, orchestrates parallel agents, and manages session memory.
- **Session Memory Store**: A first-class component that persists run history, metrics, and logs.
- **Agents**: Specialized components for code review, documentation updates, and specification tracking.
- **Frontend**: A React dashboard that visualizes the system state by consuming APIs exposed by the backend.

## Diagram

```mermaid
{diagram}
```

## Pluggable Review Architecture

The system features a **Pluggable Review Provider** layer that abstracts the underlying review engine.

**Flow:**
`GitHub Push → Orchestrator → Code Reviewer → Review Providers → (Jules API / LLM) → GitHub Feedback`

- **Primary**: **Jules / Google Code Review API** is used for high-quality, specialized code reviews.
- **Fallback**: If Jules is unavailable or fails, the system automatically falls back to **LLM Providers** (Gemini, OpenAI, Anthropic) to ensure continuity.
- **Abstraction**: The `ReviewProvider` interface ensures that `CodeReviewer`, `ReadmeUpdater`, and `SpecUpdater` are agnostic to the underlying engine.

## Live Updates

To ensure this diagram stays in sync with the codebase, use the `generate_architecture_diagram.py` script.

### Manual Generation
Run the script to update this file:
```bash
python generate_architecture_diagram.py
```

### CI/CD Integration
This file is automatically updated on every push to main via GitHub Actions.
{recent_enhancements}
"""
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Successfully updated {output_path}")
        if recent_enhancements:
            print("✓ Preserved Recent Enhancements section")
    except (IOError, OSError) as e:
        print(f"Error: Failed to write {output_path}: {e}")
        raise

if __name__ == "__main__":
    update_architecture_file()
