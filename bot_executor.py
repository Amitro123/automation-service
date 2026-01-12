"""
🤖 MCP Autonomous Bot - Full Lifecycle & PR Generation
=======================================================
Advanced autonomous engineering bot that acts as a contributor:
1. 🔧 Setup: Self-installs auditor engine
2. 🧪 Test: Runs project tests (pytest) to establish baseline
3. 📊 Audit: Generates comprehensive analysis report (Async)
4. 🛠️ Fix: Auto-remediates dead code (LOW risk only)
5. 🚀 PR: Creates a new git branch with fixes and report

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
    """ प्रि_pares environment, installs dependencies, and ensures tools exist."""
    print(f"🔧 Bot: Setting up environment...")
    
    # 1. Install Auditor if missing
    if not AUDITOR_REPO_DIR.exists():
        TARGET_LIB_DIR.mkdir(exist_ok=True)
        subprocess.run(["git", "clone", REPO_URL, str(AUDITOR_REPO_DIR)], check=True)
        print(f"   ✅ Cloned auditor to {AUDITOR_REPO_DIR}")
        
    # 2. Install dependencies (pip install)
    req_file = AUDITOR_REPO_DIR / "requirements.txt"
    if req_file.exists():
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_file), "--quiet"], check=True)

    # 3. Inject path to Python
    auditor_path = str(AUDITOR_REPO_DIR.absolute())
    if auditor_path not in sys.path:
        sys.path.insert(0, auditor_path)
        print(f"   ✅ Injected path: {auditor_path}")


def run_project_tests():
    """Runs project tests before auditing."""
    print("\n🧪 Phase 1: Running Project Tests (pytest)...")
    try:
        # Run pytest but don't fail script on error (we want the report)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests", "-q"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("   ✅ Tests Passed Successfully!")
        else:
            print("   ⚠️  Tests Failed (But continuing audit)...")
    except Exception as e:
        print(f"   ⚠️  Could not run tests: {e}")


def run_full_automation_cycle(project_root: str = "."):
    """
    Full Process: Tests -> Audit -> Fix -> PR
    """
    print(f"\n{'='*70}")
    print(f"🤖 MCP AUTOMATION BOT: Starting Full Lifecycle")
    print(f"{'='*70}\n")
    
    ensure_environment()
    
    try:
        from app.core.base_tool import BaseTool
        from app.agents.analyzer_agent import AnalyzerAgent
        from app.core.fix_orchestrator import AutoFixOrchestrator
        
        # Guard: Prevent self-scanning
        BaseTool.IGNORED_DIRECTORIES.add("external_libs")
        BaseTool.IGNORED_DIRECTORIES.add(".git")
        
        target_path = Path(project_root).resolve()

        # Step 1: Run Tests
        run_project_tests()

        # Step 2: Full Audit
        print("\n📊 Phase 2: Stress Testing & Auditing...")
        print("   Running ALL tools (Architecture, Security, Complexity)...")
        
        # Prepare reports directory
        reports_dir = target_path / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Agent (Corrected API)
        agent = AnalyzerAgent(reports_dir=reports_dir)
        
        # Run Analysis (Corrected Async Call)
        audit_result = asyncio.run(agent.analyze_project(str(target_path)))
        report_path = audit_result.report_path
        
        print(f"   ✅ Score: {audit_result.score}/100")
        print(f"   ✅ Report Generated: {report_path}")
        
        # Step 3: Auto-Fix
        print("\n🛠️  Phase 3: Auto-Remediation...")
        orchestrator = AutoFixOrchestrator(project_path=project_root)
        
        # Scan specifically for dead code
        report = orchestrator.deadcode_tool.analyze(Path(project_root))
        # Corrected method: _classify_fixes
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
                    print(f"      ⏭️  Skipping [HIGH RISK] in {item['file']}...")
        else:
            print("   ✅ No dead code found.")
        
        # Step 4: Create PR (if changes exist)
        has_report = report_path and os.path.exists(report_path)
        if fixes_applied > 0 or has_report:
            _create_pr_branch(fixes_applied)
        else:
            print("\n✅ No changes needed. Project is pristine.")

    except Exception as e:
        print(f"\n❌ CRITICAL FAILURE: {e}")
        import traceback
        traceback.print_exc()


def _create_pr_branch(fix_count):
    """Creates a new branch, commits, and pushes."""
    print("\n🚀 Phase 4: Preparing Pull Request...")
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    branch_name = f"fix/mcp-audit-{timestamp}"
    commit_msg = f"chore: MCP Bot Audit & Fixes ({fix_count} issues fixed)"

    try:
        # 1. Create new branch
        subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True)
        print(f"   🌱 Created branch: {branch_name}")
        
        # 2. Add files
        subprocess.run(["git", "add", "."], check=True)
        
        # 3. Commit
        subprocess.run(["git", "config", "user.name", "MCP Bot"], check=True)
        subprocess.run(["git", "config", "user.email", "bot@mcp.local"], check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
        print(f"   💾 Committed changes")
        
        # 4. Push (Mock)
        # Note: Actual push requires credentials.
        print(f"\n✨ SUCCESS! Branch is ready.")
        print(f"   👉 To Create PR: git push -u origin {branch_name}")
        print(f"   👉 Changes: {commit_msg}")

    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  Git operation failed: {e}")
        if e.stderr:
            print(f"   Stderr: {e.stderr}")


if __name__ == "__main__":
    run_full_automation_cycle()
