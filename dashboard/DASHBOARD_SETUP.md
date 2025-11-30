# Dashboard Setup Guide

## Overview
The StudioAI dashboard is now integrated into the automation-service project at `dashboard/`.

## Quick Start

### 1. Run the Backend (Flask)
```bash
# In the project root
python -m automation_agent.main
```
Backend runs on: http://localhost:8080

### 2. Run the Dashboard (Vite)
```bash
# In a new terminal
cd dashboard
npm run dev
```
Dashboard runs on: http://localhost:3000

## Features

The dashboard displays:
- **Test Coverage Metrics** - From pytest coverage reports
- **LLM Usage Stats** - Token consumption, costs, efficiency
- **Project Tasks** - Current development progress
- **Bugs & Issues** - Open issues from GitHub
- **Pull Requests** - Recent PRs and their status
- **Live Logs** - Real-time system logs
- **Architecture Diagram** - Mermaid visualization of system components
- **Security Status** - Bandit scan results

## API Integration

The dashboard connects to the Flask backend at `http://localhost:8080/api` for:
- `/api/metrics` - Coverage, LLM stats, security status
- `/api/logs?limit=50` - System logs
- `/api/repository/{name}/status` - Repository information

**Note**: Currently using mock data as fallback. To enable real data, the backend API endpoints need to be implemented in `webhook_server.py`.

## Configuration

### Backend (.env)
```ini
# Existing configuration
GITHUB_TOKEN=your_token
GITHUB_WEBHOOK_SECRET=your_secret
REPOSITORY_OWNER=your_username
REPOSITORY_NAME=your_repo

# LLM Provider
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key
```

### Dashboard (.env.local)
```ini
GEMINI_API_KEY=your_gemini_api_key_here
```

## Next Steps

To wire the dashboard to real backend data:

1. **Add flask-cors** to enable CORS:
   ```bash
   pip install flask-cors
   ```

2. **Update webhook_server.py** to add API endpoints:
   ```python
   from flask_cors import CORS
   
   # In __init__:
   CORS(self.app)
   
   # Add routes in _setup_routes():
   @self.app.route("/api/metrics", methods=["GET"])
   def get_metrics():
       # Return real metrics from coverage, LLM client, etc.
       pass
   ```

3. **Implement metrics collection** in the orchestrator to track:
   - Test coverage from pytest
   - LLM token usage from llm_client
   - Security scan results from Bandit
   - Task progress from spec.md

## Troubleshooting

### Dashboard not connecting to backend
- Ensure Flask backend is running on port 8080
- Check browser console for CORS errors
- Verify API endpoints are accessible: `curl http://localhost:8080/api/metrics`

### Port conflicts
- Backend: Change `PORT` in `.env`
- Dashboard: Change `server.port` in `vite.config.ts`

## Architecture

```
automation-service/
├── src/automation_agent/     # Flask backend
│   └── webhook_server.py      # Add API routes here
├── dashboard/                 # React + Vite frontend
│   ├── App.tsx               # Main dashboard UI
│   ├── services/
│   │   └── apiService.ts     # Backend API client
│   └── components/           # UI components
└── README.md
```
