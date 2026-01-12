# 🚀 Quick Start: MCP Auditor Integration

## TL;DR

```bash
# Run the integration script
python run_agent_integration.py

# Choose option 1, 2, or 3 when prompted
# 1 = Interactive cleanup
# 2 = Full audit report
# 3 = Both
```

## What Happens Behind the Scenes

### First Run (Setup Phase)
```
🔧 Setting up environment in external_libs...
✅ Created external_libs
📥 Cloning MCP Auditor from GitHub...
✅ Successfully cloned to external_libs/mcp-python-auditor
📦 Installing Auditor dependencies...
✅ Dependencies installed successfully
```

### Every Run (Execution Phase)
```
🔌 Added C:\...\external_libs\mcp-python-auditor to Python path
🔌 Connecting to AutoFixOrchestrator...

🤖 AGENT INTEGRATION SUCCESSFUL
   The MCP Auditor is now analyzing 'automation_service'
```

## Option 1: Interactive Cleanup Mission

**What it does**: Scans for dead code and asks you to approve each fix

**Example Output**:
```
🔍 Scanning for dead code...

⚠️  Found 3 fixable issue(s):
   [LOW RISK]  Unused Imports: 2
   [HIGH RISK] Functions/Variables: 1

──────────────────────────────────────────────────────────────────
[LOW RISK] Unused Import
📄 File: src/agents/base_agent.py
📍 Line: 8
🏷️  Name: typing.Optional

Context:
    6 | from typing import Dict, Any
    7 | from pathlib import Path
  → 8 | from typing import Optional
    9 | import logging
   10 | 

Delete this line? [y/N]: y
   🛠️  Applying fix... ✓ Done
```

**When to use**: When you want to clean up dead code safely with human oversight

## Option 2: Full Audit Report

**What it does**: Runs 10+ analysis tools and generates a comprehensive markdown report

**Example Output**:
```
⏳ This may take a minute...

✅ Audit Complete!
📊 Overall Score: 78/100
📄 Report ID: audit_20260112_114540
⏱️  Execution Time: 34.56s

Check the generated markdown report for detailed findings!
```

**Generated Report Includes**:
- 📊 Overall score breakdown
- 🏗️ Architecture analysis
- 🔄 Code duplication metrics
- 💀 Dead code detection
- 🧮 Complexity analysis
- 🛡️ Security vulnerabilities
- 🔐 Secret detection
- 🧪 Test coverage
- 📝 Git hygiene

**When to use**: When you need a comprehensive health check of your codebase

## Option 3: Both

Runs cleanup mission first, then full audit. Best for thorough codebase improvement.

## File Structure After First Run

```
automation_service/
├── external_libs/                    # Created automatically
│   └── mcp-python-auditor/          # Cloned from GitHub
│       ├── app/
│       │   ├── core/
│       │   │   ├── fix_orchestrator.py  # ← Used by cleanup
│       │   │   └── ...
│       │   ├── agents/
│       │   │   ├── analyzer_agent.py    # ← Used by audit
│       │   │   └── ...
│       │   └── tools/
│       └── requirements.txt
├── src/                             # Your code (analyzed)
├── tests/                           # Your tests
├── run_agent_integration.py         # ← Run this
└── .gitignore                       # ← Already excludes external_libs/
```

## Common Scenarios

### Scenario 1: Clean Codebase
```
🔍 Scanning for dead code...
✅ No dead code found. Project is clean!

Status: clean
Fixes Applied: 0
```

### Scenario 2: Found Issues, Approved Some
```
📊 DOGFOODING COMPLETE
Status: success
Fixes Applied: 5
Fixes Skipped: 2
Files Modified: 3
  • src/agents/base_agent.py
  • src/utils/helper.py
  • tests/test_agent.py

💡 Next Steps:
   1. Review changes: git diff
   2. Run tests: pytest
   3. Commit if satisfied: git add . && git commit -m 'Applied MCP Auditor fixes'
```

### Scenario 3: Full Audit on Real Project
```
📊 Overall Score: 78/100

Tool Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Structure (8/10)
   - 23 Python files analyzed
   - Well organized project structure

⚠️  Dead Code (12/15)
   - 3 unused imports
   - 1 unused function

✅ Tests (14/15)
   - Coverage: 82%
   - 45 tests passing

🛡️ Security (18/20)
   - No high-severity issues
   - 2 medium-severity warnings
```

## Safety Features

### Automatic Backups
Every fix creates a `.bak` file:
```
src/utils/helper.py       # Modified
src/utils/helper.py.bak   # Original backup
```

To restore:
```python
from app.tools.code_editor_tool import CodeEditorTool
editor = CodeEditorTool()
editor.restore_backup("src/utils/helper.py.bak")
```

### Git Integration
Always commit before running:
```bash
git add .
git commit -m "Pre-audit checkpoint"
python run_agent_integration.py
```

## Troubleshooting

### Error: Git not found
```bash
# Install Git for Windows
winget install Git.Git
```

### Error: Failed to clone repository
```bash
# Check internet connection
# Or manually clone:
mkdir external_libs
cd external_libs
git clone https://github.com/Amitro123/mcp-python-auditor.git
cd ..
python run_agent_integration.py
```

### Error: Import failed
```bash
# Check if repo was cloned correctly
ls external_libs/mcp-python-auditor/app/core/fix_orchestrator.py

# If missing, delete and retry:
rm -r external_libs
python run_agent_integration.py
```

## Advanced Usage

### Non-Interactive Mode
Edit `run_agent_integration.py` and change:
```python
result = orchestrator.run_cleanup_mission(interactive=False)
```

This auto-applies LOW-risk fixes only.

### Custom Exclusions
Create `audit.yaml` in project root:
```yaml
exclude:
  - "*/migrations/*"
  - "*/external_libs/*"
  - "__pycache__/*"
```

### Update Auditor
```bash
cd external_libs/mcp-python-auditor
git pull origin main
cd ../..
```

## Success Checklist

After running the integration:

- [ ] Reviewed `git diff` for all changes
- [ ] Ran tests: `pytest` ✅
- [ ] Checked audit score (target: >75/100)
- [ ] Committed changes in logical groups
- [ ] Updated documentation if needed

## Next Steps

1. **Add to CI/CD**: Run auditor in pre-commit hooks
2. **Track Progress**: Compare audit scores over time
3. **Custom Rules**: Add project-specific analysis rules
4. **Dashboard**: Create visualization for audit history

## Resources

- **Full Documentation**: `docs/MCP_AUDITOR_INTEGRATION.md`
- **Auditor Repo**: https://github.com/Amitro123/mcp-python-auditor
- **Integration Script**: `run_agent_integration.py`

---

**Remember**: This is dogfooding at its finest - using your own auditor to improve your own code! 🐕🍲
