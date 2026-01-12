"""
🤖 MCP Autonomous Bot - E2E Verification
=========================================
Robust verification bot that:
1. 📦 Setups environment independently
2. 🔌 Uses hybrid Import strategy (pip + path injection)
3. 📊 Runs Full Audit (Async)
4. 🛠️  Runs Auto-Fix (Low Risk)
5. 🚀 Creates PR branch

Usage:
    python bot_executor.py
"""

import sys
import subprocess
import os
import asyncio
from pathlib import Path
from datetime import datetime

# --- Configuration ---
TARGET_LIB_DIR = Path("external_libs")
AUDITOR_REPO_DIR = TARGET_LIB_DIR / "mcp-python-auditor"
REPO_URL = "https://github.com/Amitro123/mcp-python-auditor.git"


def ensure_environment():
    """Sets up auditor engine with hybrid approach (Install + Path)."""
    print(f"🔧 Bot: Setting up environment...")
    
    # 1. Clone (Skip pull to preserve our local fixes)
    if not AUDITOR_REPO_DIR.exists():
        TARGET_LIB_DIR.mkdir(exist_ok=True)
        subprocess.run(["git", "clone", REPO_URL, str(AUDITOR_REPO_DIR)], check=True)
        print(f"   ✅ Cloned auditor")
    else:
        print(f"   ℹ️  Repo exists (skipping pull to preserve local fixes)")

    # 1.5 Patch known bugs (Self-Healing the Auditor itself!)
    _patch_auditor_bugs()

    # 2. Install Dependencies via pip (reads pyproject.toml)
    # Using 'pip install .' ensures dependencies like bandit/radon are present
    print("   📦 Checking dependencies...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", str(AUDITOR_REPO_DIR), "--quiet"], 
        check=True
    )
    
    # 3. CRITICAL: Inject path to ensure 'from app...' works even if pip fails package resolution
    auditor_path = str(AUDITOR_REPO_DIR.absolute())
    if auditor_path not in sys.path:
        sys.path.insert(0, auditor_path)
        print(f"   🔌 Injected path: {auditor_path}")


def _patch_auditor_bugs():
    """Hot-patches known syntax errors in the cloned repo."""
    target_file = AUDITOR_REPO_DIR / "app/core/report_generator.py"
    if not target_file.exists():
        return
        
    try:
        content = target_file.read_text("utf-8")
        # Fix the malformed import
        if "try:\n        _write_complexity_section," in content:
            print("   🚑 Self-Healing: Patching report_generator.py syntax error...")
            new_content = content.replace(
                "try:\n        _write_complexity_section,",
                "try:\n    from app.core.enhanced_sections import (\n        _write_complexity_section,"
            )
            target_file.write_text(new_content, "utf-8")
    except Exception as e:
        print(f"   ⚠️ Patching failed: {e}")


def run_full_automation_cycle(project_root: str = "."):
    """Full E2E Cycle"""
    print(f"\n{'='*70}")
    print(f"🤖 MCP E2E BOT: Starting Verification")
    print(f"{'='*70}\n")
    
    ensure_environment()
    
    try:
        # Import Tools
        from app.core.base_tool import BaseTool
        from app.agents.analyzer_agent import AnalyzerAgent
        from app.core.fix_orchestrator import AutoFixOrchestrator
        
        # Prevent self-scan
        BaseTool.IGNORED_DIRECTORIES.add("external_libs")
        BaseTool.IGNORED_DIRECTORIES.add(".git")
        
        target_path = Path(project_root).resolve()

        # --- STEP 1: AUDIT ---
        print("\n📊 Phase 1: Full Audit...")
        
        # Ensure reports dir exists
        reports_dir = target_path / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Agent
        agent = AnalyzerAgent(reports_dir=reports_dir)
        
        # Run Async Audit
        print("   Running AnalyzerAgent (Async)...")
        audit_result = asyncio.run(agent.analyze_project(str(target_path)))
        
        score = audit_result.score
        report_path = audit_result.report_path
        
        print(f"   ✅ Audit Complete!")
        print(f"      Score: {score}/100")
        print(f"      Report: {report_path}")

        # --- STEP 2: FIX ---
        print("\n🛠️  Phase 2: Auto-Remediation...")
        orchestrator = AutoFixOrchestrator(project_path=project_root)
        
        # Scan for dead code
        report = orchestrator.deadcode_tool.analyze(Path(project_root))
        
        # Use CORRECT method: _classify_fixes
        candidates = orchestrator._classify_fixes(report)
        
        fixes_applied = 0
        if candidates:
            print(f"   🛡️  Safety Filter: [LOW RISK] fixes only.")
            for item in candidates:
                if item['risk'] == 'LOW':
                    print(f"      🔧 Fixing {item['type']} in {item['file']}...")
                    res = orchestrator.editor_tool.delete_line(
                        file_path=str(target_path / item['file']), 
                        line_number=item['line']
                    )
                    if res['status'] == 'success':
                        fixes_applied += 1
                        print("         ✓ Fixed")
                    else:
                        print(f"         ✗ Failed: {res.get('error')}")
                else:
                    print(f"      ⏭️  Skipping [HIGH RISK] in {item['file']}")
        else:
            print("   ✅ No dead code found.")
        
        # --- STEP 3: PR ---
        if fixes_applied > 0:
            _create_pr_branch(fixes_applied)
        else:
            print("\n✅ System matches baseline. E2E Test Passed.")

    except ImportError as e:
        print(f"\n❌ IMPORT ERROR: {e}")
        print("   This usually means 'app' module not found in path.")
        print(f"   Current sys.path: {sys.path[:3]}...")
    except Exception as e:
        print(f"\n❌ RUNTIME FAILURE: {e}")
        import traceback
        traceback.print_exc()


def _create_pr_branch(fix_count):
    """Creates PR branch"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    branch_name = f"fix/mcp-audit-{timestamp}"
    commit_msg = f"chore: MCP Bot Audit & Fixes ({fix_count} issues)"

    print(f"\n🚀 Phase 3: Creating PR Branch...")
    try:
        subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True)
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "config", "user.name", "MCP Bot"], check=True)
        subprocess.run(["git", "config", "user.email", "bot@mcp.local"], check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
        
        print(f"   ✅ Branch '{branch_name}' created")
        print(f"   👉 To Push: git push -u origin {branch_name}")

    except Exception as e:
        print(f"   ⚠️  Git error: {e}")


if __name__ == "__main__":
    run_full_automation_cycle()
