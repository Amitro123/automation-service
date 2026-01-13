import sys
import subprocess
import os
from pathlib import Path
from datetime import datetime
import json
import re

# --- Config ---
TARGET_LIB_DIR = Path("external_libs")
AUDITOR_REPO_DIR = TARGET_LIB_DIR / "mcp-python-auditor"
REPO_URL = "https://github.com/Amitro123/mcp-python-auditor.git"

def setup_auditor():
    """Clones and installs the Auditor (Robustly)"""
    print(f"🔧 Bot: Setting up Auditor Engine...")
    
    if not AUDITOR_REPO_DIR.exists():
        TARGET_LIB_DIR.mkdir(exist_ok=True)
        subprocess.run(["git", "clone", REPO_URL, str(AUDITOR_REPO_DIR)], check=True)
    
    # --- PATCH 1: Fix Build System (pyproject.toml) ---
    _fix_pyproject_toml()

    print("📦 Bot: Verifying dependencies...")
    # Force install dependencies
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", str(AUDITOR_REPO_DIR), "detect-secrets", "bandit", "radon"], check=True)
    except subprocess.CalledProcessError:
        print("   ⚠️ Install failed. Attempting fallback to requirements.txt...")
        req_txt = AUDITOR_REPO_DIR / "requirements.txt"
        if req_txt.exists():
             subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_txt)], check=True)
        else:
             # Fallback manual install
             subprocess.run([sys.executable, "-m", "pip", "install", "detect-secrets", "bandit", "radon", "google-generativeai", "gitpython", "fastapi"], check=True)

    # --- PATCH 2: Apply Logic Fixes ---
    _patch_report_generator()
    _patch_security_tool()

def _fix_pyproject_toml():
    """Fixes setuptools discovery error by explicitly creating a valid pyproject.toml."""
    pyproject_path = AUDITOR_REPO_DIR / "pyproject.toml"
    if not pyproject_path.exists():
        return

    print("   🔧 Bot: Patching pyproject.toml package discovery...")
    new_config = """[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mcp-python-auditor"
version = "0.2.2"
description = "AI-powered Python Code Auditor"
requires-python = ">=3.10"
dependencies = [
    "fastapi", "uvicorn", "pydantic", "google-generativeai",
    "gitpython", "pytest", "pytest-cov", "bandit", "detect-secrets", "radon"
]

[tool.setuptools]
packages = ["app"]
"""
    pyproject_path.write_text(new_config, encoding="utf-8")

def _patch_report_generator():
    """Patches syntax error in report_generator.py."""
    target_file = AUDITOR_REPO_DIR / "app/core/report_generator.py"
    if not target_file.exists(): return
    
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
        print(f"   ⚠️ Patching report_generator failed: {e}")

def _patch_security_tool():
    """Patches SecurityTool to respect ignored directories and debug Bandit."""
    target_file = AUDITOR_REPO_DIR / "app/tools/security_tool.py"
    if not target_file.exists(): return
    
    try:
        content = target_file.read_text("utf-8")
        original_content = content # Track changes
        
        # 1. Fix detect-secrets ignores
        if "exclude_patterns = get_analysis_excludes_regex()" in content:
            if "self.IGNORED_DIRECTORIES" not in content:
                print("   🚑 Bot: Patching SecurityTool to ignore external_libs...")
                old_code = "exclude_patterns = get_analysis_excludes_regex()"
                new_code = """exclude_patterns = get_analysis_excludes_regex()
        # Patch: Add dynamic ignores from BaseTool
        for ignored in self.IGNORED_DIRECTORIES:
            exclude_patterns.append(str(ignored))"""
                
                content = content.replace(old_code, new_code)

        # 2. Debug Bandit Failures
        if 'logger.error("Failed to parse Bandit output")' in content:
             print("   🚑 Bot: Adding Bandit debug logging...")
             content = content.replace(
                 'logger.error("Failed to parse Bandit output")',
                 'logger.error(f"Failed to parse Bandit output. Output was: {stdout}")'
             )
        
        if content != original_content:
            target_file.write_text(content, "utf-8")
            
    except Exception as e:
        print(f"   ⚠️ Patching SecurityTool failed: {e}")

def run_explicit_audit(project_root: str):
    """Run ALL tools manually"""
    print("\n📊 Phase 1: Running FULL Audit Suite...")
    
    if str(AUDITOR_REPO_DIR) not in sys.path:
        sys.path.append(str(AUDITOR_REPO_DIR))

    from app.core.base_tool import BaseTool
    from app.core.report_generator import ReportGenerator
    
    # Protection: Ignore sensitive dirs
    BaseTool.IGNORED_DIRECTORIES.add("external_libs")
    BaseTool.IGNORED_DIRECTORIES.add(".git")
    BaseTool.IGNORED_DIRECTORIES.add("__pycache__")
    BaseTool.IGNORED_DIRECTORIES.add("scripts")
    BaseTool.IGNORED_DIRECTORIES.add("reports")

    target_path = Path(project_root).resolve()
    results = {}
    
    # Complete Tool List
    tools_map = [
        ("app.tools.structure_tool", "StructureTool", "structure"),
        ("app.tools.deadcode_tool", "DeadcodeTool", "deadcode"), 
        ("app.tools.architecture_tool", "ArchitectureTool", "architecture"),
        ("app.tools.security_tool", "SecurityTool", "security"),
        ("app.tools.secrets_tool", "SecretsTool", "secrets"),
        ("app.tools.tests_tool", "TestsTool", "tests"),
        ("app.tools.complexity_tool", "ComplexityTool", "complexity"),
        ("app.tools.efficiency_tool", "EfficiencyTool", "efficiency"),
        ("app.tools.typing_tool", "TypingTool", "typing"),
        ("app.tools.duplication_tool", "DuplicationTool", "duplication"),
        ("app.tools.cleanup_tool", "CleanupTool", "cleanup"),
        ("app.tools.gitignore_tool", "GitignoreTool", "gitignore"),
        ("app.tools.git_tool", "GitTool", "git"), # Correct key
    ]

    for module_path, class_name, key in tools_map:
        try:
            print(f"   🔹 Running {class_name}...", end=" ", flush=True)
            module = __import__(module_path, fromlist=[class_name])
            tool_class = getattr(module, class_name)
            tool_instance = tool_class()
            
            tool_results = tool_instance.analyze(target_path)
            results[key] = tool_results
            
            if "error" in tool_results:
                print(f"⚠️  {tool_results['error']}")
            elif tool_results.get("skipped"):
                 print(f"⚠️  Skipped")
            else:
                print("✅")
                
        except ImportError:
            print(f"⚠️  Skipped (Not found)")
        except Exception as e:
            print(f"❌ Failed: {e}")
            results[key] = {"error": str(e), "status": "error"}

    print("\n📝 Generating Report...")
    reports_dir = target_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    generator = ReportGenerator(reports_dir)
    
    # Mock score for explicit run
    score = 100
    if "security" in results:
         score -= len(results["security"].get("issues", [])) * 5
    score = max(0, score)
    
    report_id = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
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
    print(f"🤖 MCP MASTER BOT: Full Diagnostic Run (v4)")
    print(f"========================================================\n")
    
    setup_auditor()
    
    if str(AUDITOR_REPO_DIR) not in sys.path:
        sys.path.append(str(AUDITOR_REPO_DIR))
    
    try:
        report_path, results = run_explicit_audit(project_root)
        
        print("\n🛠️  Phase 2: Auto-Remediation...")
        from app.core.fix_orchestrator import AutoFixOrchestrator
        
        orchestrator = AutoFixOrchestrator(project_path=project_root)
        deadcode_results = results.get("deadcode", {})
        candidates = orchestrator._classify_fixes(deadcode_results)
        
        fixes_applied = 0
        if candidates:
            print(f"🛡️  Safety Filter: [LOW RISK] fixes only.")
            for item in candidates:
                file_path_str = str(item['file']).replace("\\", "/")
                
                # Protect Critical Files
                if "external_libs" in file_path_str: continue
                if "report_generator.py" in file_path_str: continue
                if "scripts" in file_path_str: continue

                if item['risk'] == 'LOW':
                    print(f"   🔧 Fixing unused import in {item['file']}...")
                    res = orchestrator.editor_tool.delete_line(item['file'], item['line'])
                    if res['status'] == 'success':
                        fixes_applied += 1
        
        if fixes_applied > 0:
            _create_pr_branch(fixes_applied)
        else:
            print("\n✅ System Clean.")

    except Exception as e:
        print(f"❌ Critical Failure: {e}")
        import traceback
        traceback.print_exc()

def _create_pr_branch(fix_count):
    print("\n🚀 Phase 3: Creating PR Branch...")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    branch_name = f"fix/mcp-audit-{timestamp}"
    try:
        subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True)
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"chore: MCP Fixes ({fix_count}) & Report"], check=True, capture_output=True)
        print(f"   ✅ Branch '{branch_name}' created")
        print(f"   👉 To Push: git push -u origin {branch_name}")
    except Exception as e:
        print(f"   ⚠️ Git error: {e}")

if __name__ == "__main__":
    run_autonomous_cycle()
