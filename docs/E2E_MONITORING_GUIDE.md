# 🚀 E2E Monitoring Guide - PR-Centric Automation

## ✅ **What Was Just Pushed**

### **Commit:** `258dda4`
**Branch:** `feature/add-pr-creation-script`  
**PR:** #67 (existing)

### **Changes Included:**
1. ✅ **Grouped PR Feature** - All automation updates in ONE PR
2. ✅ **Gemini Usage Tracking** - Tokens, costs, provider metadata
3. ✅ **Enhanced Error Handling** - Jules 404, LLM rate limits
4. ✅ **100% Test Coverage** - 141/141 tests passing
5. ✅ **Code Cleanup** - Removed 15 temporary files

## 🎯 **Expected Automation Flow**

### **Trigger:**
Push to PR #67 → GitHub webhook → FastAPI server

### **What Should Happen:**

```
1. Webhook Received
   ├─ Signature verified ✅
   ├─ Event: pull_request (synchronized)
   └─ Trigger: pr_synchronized

2. TriggerFilter Analysis
   ├─ Diff fetched from GitHub
   ├─ Lines analyzed: code vs docs
   ├─ Trivial check: PASS (substantial changes)
   └─ Run type: full_automation

3. Parallel Tasks (Orchestrator)
   ├─ Code Review (Jules/Gemini)
   │   ├─ Fetch diff
   │   ├─ Call Jules API
   │   ├─ Post PR review comment
   │   ├─ Update AUTOMATED_REVIEWS.md
   │   └─ Log tokens + cost
   │
   ├─ README Update (Gemini)
   │   ├─ Analyze code changes
   │   ├─ Generate README updates
   │   ├─ Store content (no individual PR)
   │   └─ Log tokens + cost
   │
   └─ Spec Update (Gemini)
       ├─ Analyze commit message
       ├─ Generate spec entry
       ├─ Store content (no individual PR)
       └─ Log tokens + cost

4. Grouped PR Creation
   ├─ Branch: automation/pr-67-docs
   ├─ Commit: README.md
   ├─ Commit: spec.md
   ├─ Commit: AUTOMATED_REVIEWS.md
   └─ Create PR: "🤖 Automation updates for PR #67"

5. Session Memory Updated
   ├─ Run ID: auto-{timestamp}
   ├─ Status: completed
   ├─ Tasks: {code_review, readme_update, spec_update}
   ├─ Metrics: {tokens_used, estimated_cost}
   └─ Automation PR: #{new_pr_number}
```

## 📊 **How to Monitor**

### **Option 1: Real-Time Monitoring Script**
```bash
python monitor_automation.py
```

**Shows:**
- New runs as they happen
- Task statuses (completed/failed/skipped)
- Token usage and costs
- Automation PR numbers
- Diff analysis

### **Option 2: Check Session Memory**
```bash
cat session_memory.json | jq '.runs[0]'
```

### **Option 3: API Endpoints**
```bash
# Latest run
curl http://localhost:8080/api/history | jq '.[0]'

# Metrics
curl http://localhost:8080/api/metrics

# Logs
curl http://localhost:8080/api/logs
```

### **Option 4: GitHub UI**
1. Go to PR #67
2. Check for:
   - ✅ Jules review comment
   - ✅ New automation PR linked

## 🔍 **What to Look For**

### **✅ Success Indicators:**
- [ ] Webhook received (check server logs)
- [ ] Diff analysis shows real changes (not trivial)
- [ ] Code review posted on PR #67
- [ ] ONE automation PR created (not 3 separate PRs!)
- [ ] Automation PR contains:
  - [ ] README.md updates
  - [ ] spec.md updates
  - [ ] AUTOMATED_REVIEWS.md updates
- [ ] Session memory shows:
  - [ ] `tokens_used` > 0
  - [ ] `estimated_cost` > 0
  - [ ] `automation_pr_number` set

### **❌ Failure Indicators:**
- Multiple automation PRs created (grouped PR failed)
- `code_review: failed` status
- Empty diff or trivial skip
- No tokens logged (metadata not captured)

## 🐛 **Troubleshooting**

### **Issue: No Webhook Received**
```bash
# Check server is running
Get-Process | Where-Object {$_.ProcessName -like "*python*"}

# Check webhook URL in GitHub settings
# Should be: https://your-ngrok-url/webhook
```

### **Issue: Gemini Connection Failed**
```bash
# Check .env file
cat .env | grep GEMINI

# Verify API key
# Model: gemini-2.0-flash-lite (should work)
```

### **Issue: Multiple PRs Created**
```bash
# Check config
cat .env | grep GROUP_AUTOMATION_UPDATES
# Should be: True

# Check logs for grouped PR creation
tail -f logs/automation.log | grep "GROUPED"
```

### **Issue: No Tokens Logged**
```bash
# Check session memory
cat session_memory.json | jq '.runs[0].metrics'

# Should show:
# {
#   "tokens_used": 1234,
#   "estimated_cost": 0.0042
# }
```

## 📈 **Expected Metrics**

For this push (substantial code changes):

**Estimated Usage:**
- **Code Review:** ~800-1200 tokens
- **README Update:** ~600-900 tokens
- **Spec Update:** ~400-600 tokens
- **Total:** ~1800-2700 tokens
- **Cost:** ~$0.001-0.002 (Gemini 2.0 Flash Lite)

## 🎉 **Success Criteria**

The automation is working perfectly if:

1. ✅ **ONE grouped automation PR** created (not 3-4 separate PRs)
2. ✅ **Jules review** posted on PR #67
3. ✅ **All 3 files** in automation PR:
   - README.md
   - spec.md
   - AUTOMATED_REVIEWS.md
4. ✅ **Metrics logged** in session memory
5. ✅ **No errors** in server logs

## 🚀 **Next Steps After Verification**

Once you confirm the automation works:

1. **Merge the automation PR** to update docs
2. **Merge PR #67** to deploy the feature
3. **Monitor production** runs
4. **Implement dashboard** to display Gemini metrics
5. **Add orchestrator metric logging** (final wiring step)

## 📝 **Current Status**

- ✅ Code pushed to `feature/add-pr-creation-script`
- ✅ Server running (PID: 35128)
- ⏳ Waiting for webhook from GitHub
- 🔍 Monitoring active

**Check GitHub PR #67 for the automation PR link!**
