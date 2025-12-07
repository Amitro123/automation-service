# E2E Integration Test

**Date**: 2025-12-07  
**Purpose**: Testing frontend-backend integration with real GitHub webhooks

## Test Scenario
This test verifies the complete automation flow:
1. Push code to GitHub
2. Backend receives webhook
3. Automation tasks execute (code review, README update, spec update)
4. Dashboard updates in real-time
5. GitHub artifacts created (comments, PRs, spec entries)

## Expected Automation Tasks
- ✅ Code Review: Should post comment/issue
- ✅ README Update: Should create PR if changes detected
- ✅ Spec Update: Should append new entry to spec.md

## Services Running
- Backend: http://localhost:8080 (FastAPI)
- Frontend: http://localhost:5173 (Vite + React)

## Monitoring
Watch backend logs and dashboard for real-time updates.
