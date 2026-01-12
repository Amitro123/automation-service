"""
🧠 MCP Python Auditor Integration Script (Bridge Strategy)
===========================================================
This script integrates the "MCP Python Auditor" (the Brain) with the 
"Automation Service" project (the Body) - a dogfooding experiment!

Architecture:
    automation_service/
    ├── external_libs/          # 3rd party source code
    │   └── mcp-python-auditor/ # Cloned auditor repo
    ├── src/                    # Automation service code
    └── run_agent_integration.py # This script

Strategy:
    Instead of pip installing (which fails due to non-package structure),
    we clone the repo locally and use dynamic path injection to import it.

Usage:
    python run_agent_integration.py

What it does:
    1. Clones MCP Auditor to external_libs/mcp-python-auditor
    2. Installs auditor's dependencies
    3. Uses path injection to import AutoFixOrchestrator
    4. Runs cleanup mission on THIS project (automation_service)
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path

# --- Configuration ---
REPO_URL = "https://github.com/Amitro123/mcp-python-auditor.git"
TARGET_DIR = Path("external_libs")  # Where we keep 3rd party source code
AUDITOR_REPO_DIR = TARGET_DIR / "mcp-python-auditor"


def setup_environment():
    """Clones the auditor and installs its dependencies."""
    print(f"🔧 Setting up environment in {TARGET_DIR}...")
    
    # 1. Create target directory
    TARGET_DIR.mkdir(exist_ok=True)
    print(f"✅ Created {TARGET_DIR}")

    # 2. Clone the repo if it doesn't exist
    if not AUDITOR_REPO_DIR.exists():
        print(f"📥 Cloning MCP Auditor from {REPO_URL}...")
        try:
            subprocess.run(
                ["git", "clone", REPO_URL, str(AUDITOR_REPO_DIR)], 
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✅ Successfully cloned to {AUDITOR_REPO_DIR}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to clone repository: {e}")
            print(f"   stderr: {e.stderr}")
            sys.exit(1)
    else:
        print(f"✅ MCP Auditor repository already present at {AUDITOR_REPO_DIR}")

    # 3. Install dependencies from the Auditor's requirements.txt
    # This ensures the 'Brain' has the libraries it needs (like bandit, vulture, etc.)
    req_file = AUDITOR_REPO_DIR / "requirements.txt"
    if req_file.exists():
        print("📦 Installing Auditor dependencies...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file), "--quiet"], 
                check=True
            )
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Some dependencies may have failed to install: {e}")
            print("   Continuing anyway...")
    else:
        print(f"⚠️  No requirements.txt found at {req_file}")


def run_cleanup_mission():
    """Runs the AutoFixOrchestrator on the current project."""
    
    # 4. Dynamic Path Injection
    # We tell Python: "Look in this folder for imports too"
    auditor_path = str(AUDITOR_REPO_DIR.absolute())
    if auditor_path not in sys.path:
        sys.path.insert(0, auditor_path)
        print(f"🔌 Added {auditor_path} to Python path")

    try:
        # NOW we can import from the cloned repo as if it were local
        print("🔌 Connecting to AutoFixOrchestrator...")
        from app.core.fix_orchestrator import AutoFixOrchestrator
        
        print("\n" + "="*70)
        print("🤖 AGENT INTEGRATION SUCCESSFUL")
        print("   The MCP Auditor is now analyzing 'automation_service'")
        print("="*70 + "\n")
        
        # 5. Initialize the Orchestrator on the CURRENT project (automation_service)
        # We pass "." as the path, so it audits THIS project
        print("📂 Project Path: " + str(Path(".").absolute()))
        print("🎯 Target: Automation Service codebase")
        print("🔧 Mode: Interactive (you'll approve each fix)")
        print()
        
        orchestrator = AutoFixOrchestrator(project_path=".")
        
        # 6. Run the Mission
        print("🚀 Starting cleanup mission...")
        print("   You'll be prompted to approve/reject each suggested fix")
        print()
        
        result = orchestrator.run_cleanup_mission(interactive=True)
        
        # Display summary
        print("\n" + "="*70)
        print("📊 DOGFOODING COMPLETE")
        print("="*70)
        print(f"Status: {result['status']}")
        print(f"Fixes Applied: {result.get('fixes_applied', 0)}")
        print(f"Fixes Skipped: {result.get('fixes_skipped', 0)}")
        
        if result.get('files_modified'):
            print(f"Files Modified: {len(result['files_modified'])}")
            for file in result['files_modified']:
                print(f"  • {file}")
        
        print("\n💡 Next Steps:")
        print("   1. Review changes: git diff")
        print("   2. Run tests: pytest")
        print("   3. Commit if satisfied: git add . && git commit -m 'Applied MCP Auditor fixes'")
        print()
        
        return 0

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("   Did the repository structure change? Expected 'app.core.fix_orchestrator'.")
        print(f"   Looking in: {AUDITOR_REPO_DIR}")
        return 1
    except Exception as e:
        print(f"❌ Runtime Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def run_full_audit():
    """Bonus: Run full audit using AnalyzerAgent."""
    
    # Ensure path is injected
    auditor_path = str(AUDITOR_REPO_DIR.absolute())
    if auditor_path not in sys.path:
        sys.path.insert(0, auditor_path)
    
    try:
        print("\n" + "="*70)
        print("🔍 BONUS: Running Full Project Audit")
        print("="*70 + "\n")
        
        from app.agents.analyzer_agent import AnalyzerAgent
        
        analyzer = AnalyzerAgent()
        
        print("⏳ This may take a minute...")
        audit_result = analyzer.run_audit(".")
        
        print("\n✅ Audit Complete!")
        print(f"📊 Overall Score: {audit_result.score}/100")
        print(f"📄 Report ID: {audit_result.report_id}")
        print(f"⏱️  Execution Time: {audit_result.execution_time:.2f}s")
        print("\nCheck the generated markdown report for detailed findings!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during full audit: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point."""
    print("\n" + "="*70)
    print("🧠 MCP Python Auditor Integration (Bridge Strategy)")
    print("="*70 + "\n")
    
    # Step 1: Setup environment (clone & install)
    setup_environment()
    
    print("\n" + "="*70)
    print("Choose an option:")
    print("  1. Run Cleanup Mission (interactive dead code removal)")
    print("  2. Run Full Audit (comprehensive analysis report)")
    print("  3. Both")
    print("="*70)
    
    try:
        choice = input("\nEnter choice [1/2/3]: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n\n👋 Cancelled by user")
        return 0
    
    print()
    
    # Step 2: Execute based on choice
    if choice == "1":
        return run_cleanup_mission()
    elif choice == "2":
        return run_full_audit()
    elif choice == "3":
        exit_code = run_cleanup_mission()
        if exit_code == 0:
            exit_code = run_full_audit()
        return exit_code
    else:
        print("❌ Invalid choice. Please run again and choose 1, 2, or 3.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

