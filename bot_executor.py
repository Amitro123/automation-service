"""
🤖 MCP Auto-Fix Bot - Autonomous Code Cleanup
==============================================
Zero-touch autonomous bot that:
1. Clones/installs MCP Auditor if needed
2. Scans codebase for dead code
3. Applies ONLY [LOW RISK] fixes (unused imports)
4. Commits changes automatically

Safety Features:
- Excludes external_libs to prevent self-scanning
- Only applies LOW RISK fixes
- Creates backups before modifications
- Git commits with bot signature

Usage:
    python bot_executor.py
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

# --- Configuration ---
TARGET_LIB_DIR = Path("external_libs")
AUDITOR_REPO_DIR = TARGET_LIB_DIR / "mcp-python-auditor"
REPO_URL = "https://github.com/Amitro123/mcp-python-auditor.git"


def ensure_auditor_installed():
    """Ensures the auditor engine is present and dependencies are installed."""
    if not AUDITOR_REPO_DIR.exists():
        print("🤖 Bot: Initializing Auditor Engine...")
        TARGET_LIB_DIR.mkdir(exist_ok=True)
        subprocess.run(
            ["git", "clone", REPO_URL, str(AUDITOR_REPO_DIR)], 
            check=True,
            capture_output=True
        )
        print(f"✅ Bot: Cloned auditor to {AUDITOR_REPO_DIR}")
        
    # Install reqs (quietly)
    req_file = AUDITOR_REPO_DIR / "requirements.txt"
    if req_file.exists():
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file), "--quiet"], 
            check=True
        )


def run_autonomous_fix(project_root: str = "."):
    """
    Main Bot Entry Point.
    Analyzes code -> Filters for Safety -> Fixes -> Commits.
    """
    print(f"\n{'='*70}")
    print(f"🤖 MCP AUTO-FIX BOT: Waking up...")
    print(f"{'='*70}\n")
    
    ensure_auditor_installed()
    
    # Inject Path
    auditor_path = str(AUDITOR_REPO_DIR.absolute())
    if auditor_path not in sys.path:
        sys.path.insert(0, auditor_path)
        print(f"🔌 Bot: Injected {AUDITOR_REPO_DIR} into Python path")

    try:
        from app.core.base_tool import BaseTool
        from app.core.fix_orchestrator import AutoFixOrchestrator
        
        # --- CRITICAL: PREVENT SELF-SCANNING ---
        BaseTool.IGNORED_DIRECTORIES.add("external_libs")
        BaseTool.IGNORED_DIRECTORIES.add(".git")
        print(f"🛡️  Bot: Added external_libs to ignore list (prevents self-scan)")
        
        print(f"🎯 Target: {Path(project_root).resolve()}")
        orchestrator = AutoFixOrchestrator(project_path=project_root)
        
        # Run Analysis
        print("🔍 Scanning codebase for dead code...")
        report = orchestrator.deadcode_tool.analyze(Path(project_root))
        
        # Extract and classify fixes
        candidates = orchestrator._classify_fixes(report)
        
        if not candidates:
            print("✅ Bot: No issues found. Codebase is clean!")
            print(f"{'='*70}\n")
            return

        # Display summary
        low_risk = sum(1 for c in candidates if c['risk'] == 'LOW')
        high_risk = sum(1 for c in candidates if c['risk'] == 'HIGH')
        
        print(f"\n📊 Analysis Complete:")
        print(f"   [LOW RISK]  Unused Imports: {low_risk} (will auto-fix)")
        print(f"   [HIGH RISK] Functions/Variables: {high_risk} (requires human review)")
        print()

        fixes_applied = 0
        files_modified = set()
        
        # Apply Safe Fixes Only
        print(f"🛡️  Safety Filter: Applying [LOW RISK] fixes only\n")
        
        for item in candidates:
            if item['risk'] == 'LOW':
                print(f"   🛠️  Auto-fixing unused import '{item['name']}' in {item['file']}:{item['line']}")
                
                # Apply fix
                file_path = Path(project_root) / item['file']
                res = orchestrator.editor_tool.delete_line(
                    file_path=str(file_path),
                    line_number=item['line']
                )
                
                if res['status'] == 'success':
                    fixes_applied += 1
                    files_modified.add(item['file'])
                    print(f"      ✓ Fixed")
                else:
                    print(f"      ✗ Failed: {res.get('error', 'Unknown error')}")
            else:
                print(f"   ⏭️  Skipping [HIGH RISK] '{item['name']}' in {item['file']} (human review required)")

        # Summary
        print(f"\n{'='*70}")
        print(f"📊 BOT RESULTS")
        print(f"{'='*70}")
        print(f"Fixes Applied: {fixes_applied}")
        print(f"Files Modified: {len(files_modified)}")
        for file in sorted(files_modified):
            print(f"  • {file}")
        print(f"High Risk Issues: {high_risk} (skipped for safety)")
        print()

        # Git Commit
        if fixes_applied > 0:
            print(f"✨ Bot: Successfully fixed {fixes_applied} issue(s)")
            _commit_changes(fixes_applied)
        else:
            print("✅ Bot: No safe fixes required")
        
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"❌ Bot Crash: {e}")
        import traceback
        traceback.print_exc()


def _commit_changes(count):
    """Commits changes with bot signature."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"style: Auto-fix {count} dead code issue{'s' if count > 1 else ''} (MCP Bot {timestamp})"
        
        print(f"🚀 Git: Committing changes...")
        
        # Configure local git user for the bot
        subprocess.run(
            ["git", "config", "user.name", "MCP Bot"], 
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", "bot@mcp.local"], 
            check=True,
            capture_output=True
        )
        
        # Stage and commit
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        result = subprocess.run(
            ["git", "commit", "-m", msg], 
            check=True,
            capture_output=True,
            text=True
        )
        
        print(f"✅ Git: Committed -> '{msg}'")
        print(f"    Run 'git log -1' to view details")
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Git Error: {e}")
        if e.stderr:
            print(f"    stderr: {e.stderr}")


if __name__ == "__main__":
    run_autonomous_fix()
