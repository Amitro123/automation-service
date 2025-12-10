# Spec: StudioAI CLI & Configuration (001)

## Problem
Currently, configuring the automation agent requires manual editing of `.env` files. There is no guided onboarding, making it prone to errors. Developers need a way to easily initialize the project, configure trigger modes, and verify their setup without digging into environment variables.

## Solution
Introduce a `studioai` CLI tool that provides:
1.  **Guided Initialization**: An interactive wizard (`studioai init`) to set up the project.
2.  **Configuration Management**: Reads/writes `studioai.config.json`, serving as the source of truth (overridable by `.env`).
3.  **Status & Testing**: Commands to check system health and trigger smoke tests.
4.  **API Integration**: Exposes config via FastAPI for future MCP/Agent integration.

## User Stories

### As a Developer
- I want to run `studioai init` in a new repo and be guided through the setup (repo name, mode).
- I want a `studioai.config.json` file generated so I can commit my configuration (excluding secrets).
- I want to verify my setup by running `studioai status` or `studioai test-pr-flow`.

### As a Maintainer
- I want to switch between `pr` and `push` trigger modes easily via CLI (`studioai configure`).
- I want the dashboard to reflect the current active configuration.

## Acceptance Criteria
- [ ] `studioai init` creates a valid `studioai.config.json`.
- [ ] `studioai.config.json` settings (e.g., `TRIGGER_MODE`) take effect in the Orchestrator.
- [ ] `GET /api/config` returns the merged/effective configuration.
- [ ] Dashboard displays a "Configuration" panel with current settings.
- [ ] Push-only events are ignored when `TRIGGER_MODE=pr` is set via config file.

## Technical Details
- **CLI**: Implemented using `typer`.
- **Config**: JSON file `studioai.config.json` loaded by `config.py`.
- **Precedence**: Environment Variables > Config File > Defaults.
