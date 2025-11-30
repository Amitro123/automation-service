<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/drive/103hWMURZm-Sp7Rc9iff9FELhcPMePgJd

## StudioAI Dashboard

A React + Vite dashboard for the GitHub Automation Agent with FastAPI backend integration.

## Quick Start

### 1. Start the Backend (FastAPI)

```bash
# From project root
cd automation-service-1

# Install Python dependencies
pip install -r requirements.txt

# Run the FastAPI server
python run_api.py
# Server runs on http://localhost:8080
```

### 2. Start the Dashboard (React + Vite)

```bash
# From dashboard directory
cd dashboard
npm install
npm run dev
# Dashboard runs on http://localhost:5173
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/metrics` | GET | Dashboard metrics (coverage, LLM, tasks) |
| `/api/logs` | GET | System logs |
| `/api/repository/{name}/status` | GET | Repository status |
| `/webhook` | POST | GitHub webhook endpoint |

## Features

- **Real-time Metrics**: Test coverage, LLM token usage, cost tracking
- **Architecture Visualization**: Interactive Mermaid diagrams
- **Live Log Viewer**: Real-time system logs
- **Task Tracking**: Automation task status
- **Security Status**: Vulnerability scanning results

## Environment Variables

Create `.env` in dashboard directory:

```env
VITE_API_URL=http://localhost:8080
GEMINI_API_KEY=your_gemini_key_here
```

## Development

The Vite dev server proxies `/api` and `/webhook` requests to the FastAPI backend automatically.

## Run Locally

**Prerequisites:**  Node.js

1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`
