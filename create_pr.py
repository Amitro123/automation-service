#!/usr/bin/env python
"""Create a PR for the enhanced logging branch."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from automation_agent.config import Config
from automation_agent.github_client import GitHubClient
import asyncio

async def create_pr():
    """Create PR for enhanced logging."""
    config = Config()
    github = GitHubClient(
        token=config.GITHUB_TOKEN,
        owner=config.REPOSITORY_OWNER,
        repo=config.REPOSITORY_NAME
    )
    
    title = "🔍 Add Enhanced Webhook Logging and Diagnostic Tools"
    body = """## Purpose
This PR adds comprehensive logging and diagnostic tools to help debug the PR-centric automation flow.

## Changes

### Enhanced Logging
- **`api_server.py`**: Added `[WEBHOOK]` and `[HANDLER]` logging tags
  - Logs webhook receipt, signature verification, event details
  - Detailed PR event info (action, number, SHA, branches)
  - Background task execution tracking

- **`orchestrator.py`**: Added `[ORCHESTRATOR]` logging tags
  - Logs trigger mode configuration
  - Event classification decisions
  - Diff analysis and context creation
  - Task routing logic

### Diagnostic Tools
- **`diagnose_pr_flow.py`**: Comprehensive diagnostic script
  - Checks configuration validity
  - Verifies server health
  - Tests webhook endpoint
  - Displays SessionMemory contents
  - Sends test PR webhook

- **`check_server.py`**: Quick server health check
- **`test_webhook_pr.py`**: Manual webhook testing tool

### Documentation
- **`PR_WEBHOOK_DIAGNOSIS.md`**: Detailed diagnosis report with findings
- **`DEBUGGING_GUIDE.md`**: Quick reference guide for debugging

## Testing

### Run Diagnostics
```bash
python diagnose_pr_flow.py
```

### Expected Behavior
With this PR merged, you'll see detailed logs like:
```
[WEBHOOK] Received webhook: event=pull_request, delivery=abc123
[WEBHOOK] PR event: action=synchronize, pr=#123, title='...', head=branch@sha
[HANDLER] Processing PR #123 action=synchronize
[ORCHESTRATOR] run_automation_with_context called: event_type=pull_request
[ORCHESTRATOR] Config: TRIGGER_MODE=pr, ENABLE_PR_TRIGGER=True
[ORCHESTRATOR] TriggerContext created: trigger_type=pr_synchronized, run_type=full_automation
```

## Why This Helps

The enhanced logging provides full visibility into:
1. Whether webhooks are being received
2. How events are classified and filtered
3. Which tasks are executed and why
4. Why runs might be skipped (trivial changes)

## Testing on Real Data

Once this PR is created, push a follow-up commit to test:
1. The automation should trigger on this PR
2. Check server logs for the new logging tags
3. Verify SessionMemory has the run logged
4. Run `python diagnose_pr_flow.py` to see full diagnostics

## Related Issues

Addresses the issue where PR automation runs weren't visible - they were actually being logged correctly but skipped due to trivial change filtering.

---
**Note**: This PR contains diagnostic/debugging enhancements. The logging can be kept in production or cleaned up after debugging is complete.
"""
    
    try:
        pr_number = await github.create_pull_request(
            title=title,
            body=body,
            head="debug/enhanced-webhook-logging",
            base="main"
        )
        
        if pr_number:
            print(f"✅ PR created successfully!")
            print(f"   PR #{pr_number}")
            print(f"   URL: https://github.com/{config.get_repo_full_name()}/pull/{pr_number}")
            print()
            print("🧪 Now test the automation by pushing a commit to this branch:")
            print(f"   git checkout debug/enhanced-webhook-logging")
            print(f"   # Make a small change")
            print(f"   git commit -am 'test: Trigger automation'")
            print(f"   git push")
            print()
            print("📊 Then check:")
            print(f"   1. Server logs for [WEBHOOK], [HANDLER], [ORCHESTRATOR] tags")
            print(f"   2. SessionMemory: curl http://localhost:8080/api/history/pr/{pr_number}")
            print(f"   3. PR comments for code review")
        else:
            print("❌ Failed to create PR")
            return 1
            
    except Exception as e:
        print(f"❌ Error creating PR: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(create_pr()))
