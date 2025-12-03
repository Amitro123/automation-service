# Quick Debugging Guide for PR Automation

## 🚀 Quick Start

### Check if everything is working:
```bash
python diagnose_pr_flow.py
```

This will:
- ✅ Verify configuration
- ✅ Check server health
- ✅ Test webhook endpoint
- ✅ Show recent runs
- ✅ Send test PR webhook

---

## 🔍 Common Debugging Scenarios

### "I pushed to my PR but don't see automation running"

**Step 1**: Check if server is running
```bash
python check_server.py
```

**Step 2**: Check SessionMemory for the run
```bash
# View recent runs
curl http://localhost:8080/api/history | python -m json.tool

# Or check the file directly
cat session_memory.json | python -m json.tool
```

**Step 3**: Look for your PR number
```bash
# Get runs for specific PR
curl http://localhost:8080/api/history/pr/YOUR_PR_NUMBER | python -m json.tool
```

**Step 4**: Check if it was skipped
```bash
# Get skipped runs
curl http://localhost:8080/api/history/skipped | python -m json.tool
```

---

### "GitHub Actions run but automation doesn't"

**Possible causes**:

1. **Trivial change filter** - Your change is <10 lines
   ```bash
   # Check .env
   TRIVIAL_CHANGE_FILTER_ENABLED=True
   TRIVIAL_MAX_LINES=10
   ```
   
   **Solution**: Disable filter temporarily
   ```bash
   TRIVIAL_CHANGE_FILTER_ENABLED=False
   ```

2. **Webhook not configured** - Check GitHub webhook settings
   - Go to: Repo → Settings → Webhooks
   - Verify URL is current (ngrok URLs expire!)
   - Check "Recent Deliveries" for errors

3. **Wrong trigger mode** - Check .env
   ```bash
   TRIGGER_MODE=pr    # Only PR events
   # or
   TRIGGER_MODE=both  # PR and push events
   ```

---

### "How do I see detailed logs?"

**Server logs** (look for these tags):
- `[WEBHOOK]` - Webhook received and validated
- `[HANDLER]` - Event processing started
- `[ORCHESTRATOR]` - Automation decisions

**Example**:
```
[WEBHOOK] Received webhook: event=pull_request, delivery=abc123
[WEBHOOK] PR event: action=synchronize, pr=#123
[HANDLER] Processing PR #123 action=synchronize
[ORCHESTRATOR] TriggerContext created: trigger_type=pr_synchronized, run_type=full_automation
```

**To see logs in real-time**:
```bash
# Server terminal will show all logs
# Look for the tags above
```

---

### "How do I test without pushing to GitHub?"

**Use the test script**:
```bash
python test_webhook_pr.py
```

This sends a fake PR webhook to your local server.

**Or use the diagnostic script**:
```bash
python diagnose_pr_flow.py
```

This does a full end-to-end test.

---

## 📊 Understanding SessionMemory

SessionMemory tracks every automation run. Each run has:

```json
{
  "id": "run_abc123d_165065",
  "trigger_type": "pr_synchronized",     // How it was triggered
  "run_type": "full_automation",         // What type of run
  "status": "completed",                 // Current status
  "pr_number": 123,                      // Associated PR
  "skip_reason": "",                     // Why skipped (if applicable)
  "tasks": {                             // Task results
    "code_review": {"status": "success"},
    "readme_update": {"status": "skipped"},
    "spec_update": {"status": "success"}
  }
}
```

### Run Types

- `full_automation` - All tasks run (code review + docs)
- `partial` - Only some tasks run (e.g., docs only)
- `skipped_trivial_change` - Change too small
- `skipped_docs_only` - Only doc files changed
- `skipped_by_trigger_mode` - Event type disabled

### Statuses

- `running` - Currently executing
- `completed` - Finished successfully
- `failed` - Errors occurred
- `skipped` - Intentionally skipped
- `completed_with_issues` - Some tasks failed

---

## 🛠️ Configuration Quick Reference

### Trigger Configuration
```bash
# PR events only (recommended for PR-centric workflow)
TRIGGER_MODE=pr
ENABLE_PR_TRIGGER=True
ENABLE_PUSH_TRIGGER=False

# Both PR and push events
TRIGGER_MODE=both
ENABLE_PR_TRIGGER=True
ENABLE_PUSH_TRIGGER=True

# Push events only (legacy)
TRIGGER_MODE=push
ENABLE_PR_TRIGGER=False
ENABLE_PUSH_TRIGGER=True
```

### Trivial Change Filter
```bash
# Enable filtering (saves LLM costs)
TRIVIAL_CHANGE_FILTER_ENABLED=True
TRIVIAL_MAX_LINES=10

# Disable filtering (run on all changes)
TRIVIAL_CHANGE_FILTER_ENABLED=False
```

### PR Behavior
```bash
# Post reviews on PR (recommended)
POST_REVIEW_ON_PR=True

# Group automation PRs (recommended)
GROUP_AUTOMATION_UPDATES=True
```

---

## 🔧 Useful Commands

### Check server status
```bash
python check_server.py
```

### Run full diagnostics
```bash
python diagnose_pr_flow.py
```

### Test webhook manually
```bash
python test_webhook_pr.py
```

### View recent runs
```bash
curl http://localhost:8080/api/history
```

### View skipped runs
```bash
curl http://localhost:8080/api/history/skipped
```

### View runs for specific PR
```bash
curl http://localhost:8080/api/history/pr/123
```

### View trigger configuration
```bash
curl http://localhost:8080/api/trigger-config
```

### View dashboard metrics
```bash
curl http://localhost:8080/api/metrics
```

---

## 🐛 Troubleshooting Checklist

When automation doesn't run:

- [ ] Server is running (`python check_server.py`)
- [ ] Configuration is valid (`diagnose_pr_flow.py`)
- [ ] Webhook URL is current (check GitHub settings)
- [ ] Webhook secret matches `.env`
- [ ] PR events are enabled in webhook
- [ ] Change is not trivial (check SessionMemory)
- [ ] GitHub token has required permissions
- [ ] LLM API key is valid

---

## 📝 Next Steps

1. **Run diagnostics**: `python diagnose_pr_flow.py`
2. **Check findings**: Read `PR_WEBHOOK_DIAGNOSIS.md`
3. **Test with real PR**: Create PR with >10 lines of code changes
4. **Monitor logs**: Watch for `[WEBHOOK]`, `[HANDLER]`, `[ORCHESTRATOR]` tags
5. **Verify SessionMemory**: Check `/api/history` endpoint

---

## 💡 Pro Tips

1. **Keep server logs visible** - Run server in one terminal, test in another
2. **Use diagnostic script** - Run before each test session
3. **Check SessionMemory first** - Most "missing" runs are actually skipped
4. **Update ngrok URL** - Ngrok URLs expire, update webhook when restarting
5. **Test locally first** - Use test scripts before pushing to GitHub

---

## 📚 Related Files

- `PR_WEBHOOK_DIAGNOSIS.md` - Detailed diagnosis report
- `diagnose_pr_flow.py` - Comprehensive diagnostic tool
- `check_server.py` - Quick server health check
- `test_webhook_pr.py` - Manual webhook testing
- `session_memory.json` - Run history database
- `AGENTS.md` - Full project documentation
