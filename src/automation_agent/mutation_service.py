"""Mutation testing service using mutmut."""

import json
import logging
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Path to store mutation test results
MUTATION_RESULTS_FILE = Path("mutation_results.json")


def run_mutation_tests(max_runtime_seconds: int = 600) -> Dict[str, Any]:
    """
    Run mutation tests using mutmut and return results.
    
    Note: Mutation testing is only supported on Linux/Mac. On Windows, this will
    return a skipped status with instructions to use WSL or CI.
    
    Args:
        max_runtime_seconds: Maximum time to allow mutation tests to run
        
    Returns:
        Dictionary with mutation test results including:
        - mutation_score: Percentage of mutants killed (0-100)
        - mutants_total: Total number of mutants generated
        - mutants_killed: Number of mutants killed by tests
        - mutants_survived: Number of mutants that survived
        - mutants_timeout: Number of mutants that timed out
        - mutants_suspicious: Number of suspicious mutants
        - last_run_time: ISO timestamp of when tests were run
        - runtime_seconds: How long the tests took to run
    """
    import os
    
    # Check if running on Windows
    if os.name == 'nt':
        logger.warning("Mutation tests are not supported on Windows. Use WSL or run in CI.")
        return {
            "status": "skipped",
            "reason": "Mutation tests are only supported on Linux/Mac or CI. Use WSL or run them in a Linux CI environment.",
            "mutation_score": 0.0,
            "mutants_total": 0,
            "mutants_killed": 0,
            "mutants_survived": 0,
            "mutants_timeout": 0,
            "mutants_suspicious": 0,
            "last_run_time": datetime.now(timezone.utc).isoformat(),
            "runtime_seconds": 0.0
        }

    # Check for Python files
    if not _has_python_files():
        logger.info("No Python files found in repository. Skipping mutation tests.")
        return {
            "status": "skipped",
            "reason": "No Python files (.py) found in the repository.",
            "mutation_score": 0.0,
            "mutants_total": 0,
            "mutants_killed": 0,
            "mutants_survived": 0,
            "mutants_timeout": 0,
            "mutants_suspicious": 0,
            "last_run_time": datetime.now(timezone.utc).isoformat(),
            "runtime_seconds": 0.0
        }
    
    logger.info("Starting mutation tests with mutmut...")
    start_time = time.time()
    
    try:
        # Clean previous mutmut cache
        run_result = subprocess.run(
            ["mutmut", "run", "--paths-to-mutate=src/automation_agent", "--runner=pytest"],
            timeout=max_runtime_seconds,
            capture_output=True,
            text=True,
            check=False  # Don't raise on non-zero exit (mutmut returns non-zero if mutants survive)
        )
        
        logger.info(f"Mutmut run completed with exit code: {run_result.returncode}")
        if run_result.stderr:
            logger.warning(f"Mutmut stderr: {run_result.stderr[:500]}")
        
        # Get results summary
        result = subprocess.run(
            ["mutmut", "results"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False  # Don't raise on non-zero exit
        )
        
        if result.returncode != 0:
            logger.warning(f"Mutmut results returned non-zero exit code: {result.returncode}")
            logger.warning(f"Stdout: {result.stdout[:500]}")
            logger.warning(f"Stderr: {result.stderr[:500]}")
        
        # Parse the output
        mutation_data = _parse_mutmut_output(result.stdout)
        
        # Add metadata
        runtime = time.time() - start_time
        mutation_data["last_run_time"] = datetime.now(timezone.utc).isoformat()
        mutation_data["runtime_seconds"] = round(runtime, 2)
        
        # Save results to file
        with open(MUTATION_RESULTS_FILE, "w") as f:
            json.dump(mutation_data, f, indent=2)
        
        logger.info(f"Mutation tests completed. Score: {mutation_data['mutation_score']}%")
        return mutation_data
        
    except subprocess.TimeoutExpired:
        logger.error(f"Mutation tests exceeded timeout of {max_runtime_seconds}s")
        return {
            "error": "Mutation tests timed out",
            "mutation_score": 0.0,
            "mutants_total": 0,
            "mutants_killed": 0,
            "mutants_survived": 0,
            "mutants_timeout": 0,
            "mutants_suspicious": 0,
            "last_run_time": datetime.now(timezone.utc).isoformat(),
            "runtime_seconds": max_runtime_seconds
        }
    except Exception as e:
        logger.error(f"Error running mutation tests: {e}")
        return {
            "error": str(e),
            "mutation_score": 0.0,
            "mutants_total": 0,
            "mutants_killed": 0,
            "mutants_survived": 0,
            "mutants_timeout": 0,
            "mutants_suspicious": 0,
            "last_run_time": datetime.now(timezone.utc).isoformat(),
            "runtime_seconds": round(time.time() - start_time, 2)
        }


def _parse_mutmut_output(output: str) -> Dict[str, Any]:
    """
    Parse mutmut results output to extract mutation statistics.
    
    Expected format:
    Survived 🙁: 10
    Killed ⚔️: 90
    Timeout ⏰: 2
    Suspicious 🤔: 1
    
    Args:
        output: Raw output from 'mutmut results' command
        
    Returns:
        Dictionary with parsed mutation statistics
    """
    killed = 0
    survived = 0
    timeout = 0
    suspicious = 0
    
    for line in output.split('\n'):
        line = line.strip()
        if 'Killed' in line or '⚔️' in line:
            # Extract number before the emoji/text
            parts = line.split(':')
            if len(parts) == 2:
                try:
                    killed = int(parts[1].strip())
                except ValueError:
                    pass
        elif 'Survived' in line or '🙁' in line:
            parts = line.split(':')
            if len(parts) == 2:
                try:
                    survived = int(parts[1].strip())
                except ValueError:
                    pass
        elif 'Timeout' in line or '⏰' in line:
            parts = line.split(':')
            if len(parts) == 2:
                try:
                    timeout = int(parts[1].strip())
                except ValueError:
                    pass
        elif 'Suspicious' in line or '🤔' in line:
            parts = line.split(':')
            if len(parts) == 2:
                try:
                    suspicious = int(parts[1].strip())
                except ValueError:
                    pass
    
    total = killed + survived + timeout + suspicious
    mutation_score = (killed / total * 100) if total > 0 else 0.0
    
    return {
        "mutation_score": round(mutation_score, 1),
        "mutants_total": total,
        "mutants_killed": killed,
        "mutants_survived": survived,
        "mutants_timeout": timeout,
        "mutants_suspicious": suspicious
    }


def get_latest_results() -> Optional[Dict[str, Any]]:
    """
    Read the latest mutation test results from file.
    
    Returns:
        Dictionary with mutation results, or None if no results available
    """
    if not MUTATION_RESULTS_FILE.exists():
        return None
    
    try:
        with open(MUTATION_RESULTS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading mutation results: {e}")
        return None


def _has_python_files() -> bool:
    """Check if there are any .py files in the repository."""
    import os
    for root, dirs, files in os.walk("."):
        if "venv" in dirs:
            dirs.remove("venv")
        if ".git" in dirs:
            dirs.remove(".git")
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
            
        for file in files:
            if file.endswith(".py"):
                return True
    return False
