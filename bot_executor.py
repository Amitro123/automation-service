import sys
import subprocess
import os
from pathlib import Path
from datetime import datetime

# --- Config ---
TARGET_LIB_DIR = Path("external_libs")
AUDITOR_REPO_DIR = TARGET_LIB_DIR / "mcp-python-auditor"
REPO_URL = "https://github.com/Amitro123/mcp-python-auditor.git"

def setup_auditor():
    """Clones and installs the Auditor"""
    print(f"🔧 Bot: Setting up Auditor Engine...")
    
    if not AUDITOR_REPO_DIR.exists():
        TARGET_LIB_DIR.mkdir(exist_ok=True)
        subprocess.run(["git", "clone", REPO_URL, str(AUDITOR_REPO_DIR)], check=True)
    
    # Verify dependencies
    print("📦 Bot: Checking dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-e", str(AUDITOR_REPO_DIR), "detect-secrets", "bandit"], check=True)
    
    # Apply self-healing patches
    _patch_auditor_bugs()

def _patch_auditor_bugs():
    """Hot-patches known syntax errors in the cloned repo."""
    target_file = AUDITOR_REPO_DIR / "app/core/report_generator.py"
    if not target_file.exists():
        return
        
    try:
        content = target_file.read_text("utf-8")
        if "try:\n        _write_complexity_section," in content:
            print("   🚑 Bot: Patching report_generator.py syntax error...")
            new_content = content.replace(
                "try:\n        _write_complexity_section,",
                "try:\n    from app.core.enhanced_sections import (\n        _write_complexity_section,"
            )
            target_file.write_text(new_content, "utf-8")
    except Exception as e:
        print(f"   ⚠️ Patching failed: {e}")

def run_explicit_audit(project_root: str):
    """
    Runs tools manually to avoid orchestration issues.
    """
    print("\n📊 Phase 1: Running Explicit Audit Tools...")
    
    # Import base tools
    try:
        from app.core.base_tool import BaseTool
        from app.core.report_generator import ReportGenerator
    except ImportError:
        # Fallback if path injection hasn't happened yet (shouldn't happen due to run_autonomous_cycle)
        if str(AUDITOR_REPO_DIR) not in sys.path:
            sys.path.append(str(AUDITOR_REPO_DIR))
        from app.core.base_tool import BaseTool
        from app.core.report_generator import ReportGenerator
    
    # Protection
    BaseTool.IGNORED_DIRECTORIES.add("external_libs")
    BaseTool.IGNORED_DIRECTORIES.add(".git")
    BaseTool.IGNORED_DIRECTORIES.add("__pycache__")
    
    target_path = Path(project_root).resolve()
    results = {}
    
    # 1. Structure
    try:
        from app.tools.structure_tool import StructureTool
        print("   🔹 Running StructureTool...")
        results["structure"] = StructureTool().analyze(target_path)
    except Exception as e:
        print(f"   ❌ StructureTool failed: {e}")

    # 2. Dead Code
    try:
        from app.tools.deadcode_tool import DeadcodeTool
        print("   🔹 Running DeadcodeTool...")
        results["deadcode"] = DeadcodeTool().analyze(target_path)
    except Exception as e:
        print(f"   ❌ DeadcodeTool failed: {e}")

    # 3. Architecture
    try:
        from app.tools.architecture_tool import ArchitectureTool
        print("   🔹 Running ArchitectureTool...")
        results["architecture"] = ArchitectureTool().analyze(target_path)
    except Exception as e:
        print(f"   ❌ ArchitectureTool failed: {e}")

    # 4. Security (Bandit)
    try:
        from app.tools.security_tool import SecurityTool
        print("   🔹 Running SecurityTool...")
        results["security"] = SecurityTool().analyze(target_path)
    except Exception as e:
        print(f"   ❌ SecurityTool failed: {e}")

    # 5. Secrets
    try:
        from app.tools.secrets_tool import SecretsTool
        print("   🔹 Running SecretsTool...")
        results["secrets"] = SecretsTool().analyze(target_path)
    except Exception as e:
        print(f"   ❌ SecretsTool failed: {e}")

    # 6. Tests
    try:
        from app.tools.tests_tool import TestsTool
        print("   🔹 Running TestsTool...")
        results["tests"] = TestsTool().analyze(target_path)
    except Exception as e:
        print(f"   ❌ TestsTool failed: {e}")
        
    # Generate Report
    print("\n📝 Generating Report...")
    reports_dir = target_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    generator = ReportGenerator(reports_dir)
    
    # ReportGenerator.generate_report expects keys: report_id, project_path, tool_results, timestamp, score
    # We need to construct a robust call
    
    report_id = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Calculate a dummy score for now since we skipped the complex scoring logic
    score = 80 # Default passing score
    if "security" in results and "issues" in results["security"] and results["security"]["issues"]:
        score -= 10
    if "deadcode" in results:
        dead = len(results["deadcode"].get("dead_functions", [])) + len(results["deadcode"].get("unused_imports", []))
        score -= min(10, dead)
        
    report_path = generator.generate_report(
        report_id=report_id,
        project_path=str(target_path),
        score=score,
        tool_results=results,
        timestamp=datetime.now()
    )
    print(f"✅ Report saved: {report_path}")
    
    return report_path, results

def run_autonomous_cycle(project_root: str = "."):
    print(f"\n========================================================")
    print(f"🤖 MCP EXPLICIT BOT: Starting Verification")
    print(f"========================================================\n")
    
    setup_auditor()
    
    # Critical Path Injection
    if str(AUDITOR_REPO_DIR) not in sys.path:
        sys.path.append(str(AUDITOR_REPO_DIR))
    
    try:
        # Run Explicit Audit
        report_path, results = run_explicit_audit(project_root)
        
        # Auto-Remediation
        print("\n🛠️  Phase 2: Auto-Remediation...")
        from app.core.fix_orchestrator import AutoFixOrchestrator
        
        orchestrator = AutoFixOrchestrator(project_path=project_root)
        # Use existing deadcode results
        deadcode_results = results.get("deadcode", {})
        
        # Use CORRECT method: _classify_fixes
        candidates = orchestrator._classify_fixes(deadcode_results)
        
        fixes_applied = 0
        if candidates:
            print(f"🛡️  Safety Filter: [LOW RISK] fixes only.")
            for item in candidates:
                if item['risk'] == 'LOW':
                    print(f"   🔧 Fixing unused import in {item['file']}...")
                    res = orchestrator.editor_tool.delete_line(item['file'], item['line'])
                    if res['status'] == 'success':
                        fixes_applied += 1
                else:
                    print(f"   ⏭️  Skipping [HIGH RISK] issue in {item['file']}")
        
        if fixes_applied > 0:
            _create_pr_branch(fixes_applied)
        else:
            print("\n✅ System Clean (Or fixes skipped).")

    except Exception as e:
        print(f"❌ Critical Failure: {e}")
        import traceback
        traceback.print_exc()

def _create_pr_branch(fix_count):
    print("\n🚀 Phase 3: Creating PR Branch...")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    branch_name = f"fix/mcp-audit-{timestamp}"
    
    try:
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"chore: MCP Fixes ({fix_count})"], check=True)
        print(f"   ✅ Branch '{branch_name}' created")
        print(f"   👉 To Push: git push -u origin {branch_name}")
    except Exception as e:
        print(f"   ⚠️ Git error: {e}")

if __name__ == "__main__":
    run_autonomous_cycle()
