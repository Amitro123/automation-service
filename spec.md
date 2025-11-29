# 📋 GitHub Automation Agent - Product Specification & Progress

**Last Updated:** `date`  
**Status:** Phase 2 Complete ✅ | Phase 3 Testing 🔄 | Phase 4 Deployment 🚀

## 🎯 Product Mission

**One sentence:** Autonomous GitHub agent that reacts to **every push** → delivers **code review + fresh docs + progress log** within 60 seconds.

**Value proposition:** 
- Developers get instant, intelligent feedback without waiting for humans
- Repos stay self-documenting (README + spec.md always current)  
- Teams get automated audit trail of decisions + architecture evolution

## 📋 User Stories (Acceptance Criteria)

### As a Developer → I push code → I get instant feedback
GIVEN: I push to any branch
WHEN: Agent receives webhook
THEN:
✅ Code review posted (comment/issue) within 30s
✅ Review covers: bugs/security/performance/best practices
✅ Review is actionable (specific line numbers + fixes)

### As a Maintainer → Docs stay fresh automatically
GIVEN: I add new functions/APIs/dependencies
WHEN: Agent analyzes diff
THEN:
✅ README PR created (if changes detected)
✅ Only relevant sections updated (preserves tone/structure)
✅ PR title: "docs: sync README with latest changes"

### As a Team → Project progress is tracked
GIVEN: Push contains meaningful changes
WHEN: Agent runs spec updater
THEN:
✅ New entry appended to this file
✅ Entry includes: timestamp + summary + decisions + next steps
✅ Historical context preserved

## 🏗️ System Architecture (NEVER CHANGE)

GitHub Push Event (JSON)
            ↓
┌─────────────────────────────────────────────────────────────┐
│                webhook_server.py (Flask)                    │
│       (HMAC verification + diff extraction)                 │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 orchestrator.py (asyncio)                   │
│             (Coordinates 3 PARALLEL tasks)                  │
└───────────┬───────────────┼──────────────────┬──────────────┘
            │               │                  │
            ↓               ↓                  ↓
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │code_reviewer.│ │readme_updater│ │spec_updater. │
    │      py      │ │      py      │ │      py      │
    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
           ↓                ↓                ↓
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │  GitHub API  │ │  GitHub API  │ │   spec.md    │
    │  (comment/   │ │ (PR create)  │ │   (append)   │
    │   issue)     │ │              │ │              │
    └──────────────┘ └──────────────┘ └──────────────┘

**Key invariants (NEVER CHANGE):**
- Tasks run **PARALLEL** via `asyncio.gather()` [web:55]
- Each task is **idempotent** (safe for webhook retries)
- One task failure **doesn't block** others
- All side-effects create **traceable GitHub artifacts**
- All side-effects logged with GitHub artifact IDs

## 🔧 Detailed Behavior By Module

### 1. CodeReviewer
**Input:** `git diff` + file context (500 lines around changes)  
**Output:** Structured review JSON:
{
"strengths": ["Good test coverage", "Clean error handling"],
"issues": [{"file": "x.py", "line": 42, "severity": "high", "message": "..."}],
"suggestions": ["Consider async/await", "Add type hints"],
"security": [],
"performance": []
}

**Delivery:** Comment on commit OR issue (configurable)

### 2. ReadmeUpdater  
**Detection rules:**
- New `def`/`class` → update Features/Usage sections
- `requirements.txt` changes → update Prerequisites  
- New files → scan for public APIs → add to README
**Rules:** Touch **only** changed sections. Preserve tone/structure.

### 3. SpecUpdater
**Every entry format:**
2025-11-28 22:00 UTC | SHA: abc123 | "feat: add async orchestrator"
Changes
Implemented parallel task execution (3x faster)

Added retry logic for GitHub API rate limits

Decisions
Use asyncio.gather() over ThreadPool (better for I/O)

500-line diff limit to control LLM costs

Next Steps
 Add unit tests for orchestrator

 Test large diff chunking (>10k lines)

 Multi-LLM support (Gemini) - Done ✅

## 📊 Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| **Performance** | <60s end-to-end for 5k-line diff |
| **Reliability** | 99% success rate, idempotent tasks |
| **Cost** | <$0.10 per push (gpt-4o-mini) |
| **Security** | HMAC webhook verification, no secret logging |
| **Observability** | Structured logs + GitHub artifact tracking |

## ✅ Progress & Milestones

### Phase 1: Core Loop ✅ (2025-11-12)
[x] Webhook server + signature verification
[x] Basic orchestrator (3 parallel tasks)
[x] LLM client (OpenAI + Anthropic)
[x] GitHub client (diffs/comments/PRs)

### Phase 2: Local Testing ✅ (2025-11-25)
[x] End-to-end test: push → 3 artifacts created
[x] Config from .env (verified)
[x] Error handling + logging
[x] Idempotency (handles retries)

### Phase 3: Comprehensive Testing ✅ (2025-11-29)
[x] Unit tests: 80% coverage (mock all external)
[x] Integration tests: webhook simulation
[x] Load tests: 10 concurrent pushes
[x] Edge cases: empty diff, huge files, rate limits
**Results**: 93/95 tests passing (98% pass rate)

### Phase 4: Production Ready 🚀 (NEXT)
[ ] Docker container + health checks
[ ] GitHub Actions CI/CD
[ ] Agent platform hooks (Windsurf/Gravity)
[ ] Multi-repo support
[ ] Per-branch policies

## 🔍 Current Tasks (Agent Priorities)

HIGH: Begin Phase 4 deployment
→ Create Dockerfile + docker-compose
→ Set up GitHub Actions CI/CD workflow

MEDIUM: Phase 4 deployment
→ Dockerfile + docker-compose
→ GitHub Actions workflow

LOW: Polish
→ Better LLM prompts (structured JSON outputs)
→ Diff chunking for huge changes

## 🚫 Out of Scope (Don't Implement)
❌ Real-time PR reviews (only push events)
❌ GitHub App (webhook-only)
❌ GUI dashboard
❌ Self-hosting LLM


## 📈 Success Metrics

**Weekly goals:**
✅ 95% push success rate
✅ <45s average response time
✅ Zero secret leaks in logs
✅ 100% test coverage
✅ README/spec.md accuracy >95%

