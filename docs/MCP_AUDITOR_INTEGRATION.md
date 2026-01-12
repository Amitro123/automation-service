# 🧠 MCP Python Auditor Integration Guide

## Overview

This document explains how to integrate and use the **MCP Python Auditor** (the "Brain") to analyze and improve the **Automation Service** project (the "Body").

The MCP Python Auditor is a powerful static analysis engine that can:
- 🔍 Detect dead code (unused imports, functions, variables)
- 🛡️ Identify security vulnerabilities
- 📊 Analyze code complexity and quality
- 🧹 Suggest and apply automated fixes
- 📝 Generate comprehensive audit reports

## Installation

### Option 1: Install from GitHub (Recommended)

```bash
pip install git+https://github.com/Amitro123/mcp-python-auditor.git
```

### Option 2: Install Dependencies Only

If you want to install dependencies without the auditor itself:

```bash
pip install -r requirements.txt
```

Then install the auditor separately:

```bash
pip install git+https://github.com/Amitro123/mcp-python-auditor.git
```

## Quick Start

### 1. Run the Integration Script

```bash
python run_agent_integration.py
```

You'll be presented with three options:
- **Option 1**: Run Cleanup Mission (interactive dead code removal)
- **Option 2**: Run Full Audit (comprehensive analysis report)
- **Option 3**: Both

### 2. Choose Your Adventure

#### 🧹 **Cleanup Mission** (Option 1)

The Cleanup Mission uses `AutoFixOrchestrator` to:
1. Scan for dead code (unused imports, functions, variables)
2. Classify findings by risk level (LOW/HIGH)
3. Present each finding interactively
4. Apply fixes with your approval
5. Create `.bak` backups automatically

**Example Flow:**
```
🔍 Scanning for dead code...
⚠️  Found 5 fixable issue(s):
   [LOW RISK]  Unused Imports: 3
   [HIGH RISK] Functions/Variables: 2

──────────────────────────────────────────────────────────────────
[LOW RISK] Unused Import
📄 File: src/utils/helper.py
📍 Line: 5
🏷️  Name: os

Context:
    3 | import sys
    4 | import json
  → 5 | import os
    6 | import requests
    7 | 

Delete this line? [y/N]: y
   🛠️  Applying fix... ✓ Done
```

#### 🔍 **Full Audit** (Option 2)

The Full Audit uses `AnalyzerAgent` to:
1. Run 10+ analysis tools in parallel
2. Calculate an overall project score (0-100)
3. Generate a detailed Markdown report
4. Identify issues across all categories:
   - Code structure & architecture
   - Duplication & dead code
   - Complexity & efficiency
   - Security & secrets
   - Test coverage
   - Git hygiene

**Example Output:**
```
✅ Audit Complete!
📊 Overall Score: 82/100
📄 Report ID: audit_20260112_113952
⏱️  Execution Time: 23.45s

Check the generated markdown report for detailed findings!
```

## Architecture Integration

### How the "Brain" Analyzes the "Body"

```
┌─────────────────────────────────────────────────────────────┐
│                    Automation Service                        │
│                      (The "Body")                            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           run_agent_integration.py                    │  │
│  │               (Integration Layer)                     │  │
│  └───────────────────┬──────────────────────────────────┘  │
│                      │                                      │
│                      ▼                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         MCP Python Auditor (The "Brain")             │  │
│  │                                                       │  │
│  │  ┌─────────────────────┐  ┌────────────────────┐    │  │
│  │  │ AutoFixOrchestrator │  │  AnalyzerAgent     │    │  │
│  │  │ (Interactive Fixes) │  │  (Full Audit)      │    │  │
│  │  └─────────────────────┘  └────────────────────┘    │  │
│  │                                                       │  │
│  │  ┌───────────────────────────────────────────────┐  │  │
│  │  │           Tool Registry                        │  │  │
│  │  │  • DeadcodeTool    • SecurityTool             │  │  │
│  │  │  • ComplexityTool  • SecretsTool              │  │  │
│  │  │  • TestsTool       • CleanupTool              │  │  │
│  │  │  • GitTool         • ArchitectureTool         │  │  │
│  │  └───────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                      ▲                                      │
│                      │                                      │
│              Scans & Analyzes                               │
│                      │                                      │
│  ┌───────────────────┴──────────────────────────────────┐  │
│  │         Automation Service Codebase                   │  │
│  │  • src/       • tests/       • docs/                  │  │
│  │  • scripts/   • dashboard/   • specs/                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. `AutoFixOrchestrator`
- **Location**: `app/core/fix_orchestrator.py` (in mcp-python-auditor)
- **Purpose**: Interactive code cleanup with user approval
- **Features**:
  - Risk classification (LOW/HIGH)
  - Line-by-line context display
  - Automatic backup creation (`.bak` files)
  - Safe file editing with `CodeEditorTool`

#### 2. `AnalyzerAgent`
- **Location**: `app/agents/analyzer_agent.py` (in mcp-python-auditor)
- **Purpose**: Comprehensive project analysis
- **Features**:
  - 10+ specialized analysis tools
  - Parallel tool execution
  - Weighted scoring algorithm
  - Markdown report generation
  - Self-healing capabilities

#### 3. Tool Registry
- **Location**: `app/core/tool_registry.py` (in mcp-python-auditor)
- **Purpose**: Plugin architecture for extensible analysis
- **Available Tools**:
  - `StructureTool` - Project organization
  - `ArchitectureTool` - Design patterns
  - `DuplicationTool` - Code clones
  - `DeadcodeTool` - Unused code
  - `ComplexityTool` - Cyclomatic complexity
  - `CleanupTool` - Code smells
  - `SecurityTool` - Vulnerability scanning (Bandit)
  - `SecretsTool` - Credential detection
  - `TestsTool` - Coverage analysis
  - `GitignoreTool` - Git hygiene

## Advanced Usage

### Programmatic Integration

You can also use the auditor programmatically in your own scripts:

```python
from app.core.fix_orchestrator import AutoFixOrchestrator
from app.agents.analyzer_agent import AnalyzerAgent

# Cleanup mission
orchestrator = AutoFixOrchestrator(project_path=".")
result = orchestrator.run_cleanup_mission(interactive=False)  # Auto mode
print(f"Applied {result['fixes_applied']} fixes")

# Full audit
analyzer = AnalyzerAgent()
audit_result = analyzer.run_audit(".")
print(f"Score: {audit_result.score}/100")
```

### Custom Tool Configuration

The auditor can be configured via `audit.yaml` (create in project root):

```yaml
tools:
  # Enable/disable specific tools
  security:
    enabled: true
    timeout: 30
  
  tests:
    enabled: true
    coverage_threshold: 80
  
  complexity:
    enabled: true
    max_complexity: 10

# Exclusion patterns
exclude:
  - "*/migrations/*"
  - "*/venv/*"
  - "*/node_modules/*"
  - "__pycache__/*"
  - "*.pyc"
```

## Best Practices

### Before Running

1. **Commit your work**: Always commit or stash changes before running fixes
   ```bash
   git add .
   git commit -m "Pre-audit checkpoint"
   ```

2. **Run tests first**: Ensure your tests pass before applying fixes
   ```bash
   pytest
   ```

3. **Review backups**: The orchestrator creates `.bak` files - keep them until you verify fixes

### After Running

1. **Review changes**: Use `git diff` to review all modifications
   ```bash
   git diff
   ```

2. **Run tests**: Verify fixes didn't break functionality
   ```bash
   pytest
   npm test  # if applicable
   ```

3. **Update documentation**: If structural changes were made, update docs

4. **Commit selectively**: Commit fixes in logical groups
   ```bash
   git add src/utils/helper.py
   git commit -m "Remove unused imports from helper.py"
   ```

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError: No module named 'app'`:

```bash
# Ensure mcp-python-auditor is installed
pip install git+https://github.com/Amitro123/mcp-python-auditor.git

# Verify installation
python -c "from app.core.fix_orchestrator import AutoFixOrchestrator; print('✅ Installed')"
```

### Tool Failures

If specific tools fail during audit:

1. Check missing dependencies (e.g., `pytest-cov`, `bandit`)
2. Review tool timeouts in logs
3. Check exclusion patterns in `audit.yaml`

### Performance Issues

For large projects:

1. Run in non-interactive mode: `orchestrator.run_cleanup_mission(interactive=False)`
2. Increase tool timeouts in `audit.yaml`
3. Use exclusion patterns to skip large directories (e.g., `venv/`, `node_modules/`)

## Integration Roadmap

### ✅ Phase 1: Initial Integration (Current)
- Install auditor from GitHub
- Run standalone cleanup missions
- Generate audit reports

### 🔄 Phase 2: CI/CD Integration (Next)
- Add pre-commit hooks for automatic cleanup
- Integrate audit reports into PR reviews
- Set up automated quality gates

### 🚀 Phase 3: Deep Integration (Future)
- Embed auditor as FastAPI dependency
- Create dashboard for audit history
- Implement continuous monitoring
- Add custom automation-service specific rules

## Resources

- **Auditor Repository**: https://github.com/Amitro123/mcp-python-auditor
- **Integration Script**: `run_agent_integration.py`
- **Tool Documentation**: See auditor's `README.md`

## Support

For issues or questions:
1. Check the auditor's GitHub issues
2. Review this integration guide
3. Consult the main `README.md` for project-specific context

---

**Remember**: The MCP Python Auditor is the "Brain" that analyzes our "Body" (automation-service). 
Use it wisely to maintain code quality and catch issues early! 🧠✨
