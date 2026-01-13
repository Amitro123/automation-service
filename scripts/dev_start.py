#!/usr/bin/env python
"""
Unified development startup script.
Starts backend, ngrok, and frontend together for E2E testing.

Usage:
    python scripts/dev_start.py

Press Ctrl+C to stop all services.
"""

import os
import sys
import subprocess
import signal
import time
import threading
import re
import shutil
import logging
from pathlib import Path

# Configure logging for debug output
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Colors for terminal output
class Colors:
    BACKEND = "\033[94m"  # Blue
    NGROK = "\033[92m"    # Green
    FRONTEND = "\033[93m" # Yellow
    ERROR = "\033[91m"    # Red
    RESET = "\033[0m"
    BOLD = "\033[1m"


# Configure ngrok path - update this if ngrok is not in PATH
NGROK_PATH = r"C:\Users\USER\Downloads\ngrok-v3-stable-windows-amd64\ngrok.exe"


def print_colored(prefix: str, message: str, color: str):
    """Print a colored message with prefix."""
    print(f"{color}[{prefix}]{Colors.RESET} {message}")


def stream_output(process, prefix: str, color: str):
    """Stream process output with colored prefix."""
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                print_colored(prefix, line.rstrip(), color)
    except Exception as e:
        # Log stream termination for debugging (process may have exited normally)
        logging.debug(f"Output stream for {prefix} ended: {e}")


def find_ngrok_url(process, timeout: int = 15) -> str | None:
    """Wait for ngrok to start and extract the public URL."""
    start_time = time.time()
    
    # Try to get URL from ngrok's API
    while time.time() - start_time < timeout:
        try:
            import urllib.request
            import json
            
            with urllib.request.urlopen("http://localhost:4040/api/tunnels", timeout=2) as response:
                data = json.loads(response.read().decode())
                tunnels = data.get("tunnels", [])
                for tunnel in tunnels:
                    if tunnel.get("proto") == "https":
                        return tunnel.get("public_url")
                    elif tunnel.get("public_url"):
                        return tunnel.get("public_url")
        except Exception as e:
            # Expected during ngrok startup - polling until API is ready
            logging.debug(f"Waiting for ngrok API: {e}")
        
        time.sleep(1)
    
    return None


def get_ngrok_command() -> str | None:
    """Get the ngrok command/path to use."""
    # First check the configured path
    if os.path.exists(NGROK_PATH):
        return NGROK_PATH
    
    # Then check if ngrok is in PATH
    try:
        result = subprocess.run(
            ["ngrok", "version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return "ngrok"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return None


def get_npm_path() -> str | None:
    """
    Safely resolve the full path to npm executable.
    
    Security Note: Using shutil.which() instead of relying on PATH lookup
    at subprocess execution time. This is safer as it resolves the path
    once at startup in a controlled manner.
    """
    return shutil.which("npm")


def check_npm_installed() -> bool:
    """Check if npm is installed and get its path."""
    npm_path = get_npm_path()
    if not npm_path:
        return False
    
    try:
        result = subprocess.run(
            [npm_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5
            # shell=False (default) - safer, using resolved path
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def main():
    project_root = Path(__file__).parent.parent.absolute()
    dashboard_dir = project_root / "dashboard"
    
    processes = []
    
    print(f"\n{Colors.BOLD}🚀 Starting GitHub Automation Agent - Dev Mode{Colors.RESET}\n")
    print(f"Project root: {project_root}\n")
    
    # Check prerequisites
    if not check_npm_installed():
        print_colored("ERROR", "npm is not installed! Please install Node.js first.", Colors.ERROR)
        print("Download from: https://nodejs.org/")
        sys.exit(1)
    
    ngrok_cmd = get_ngrok_command()
    if not ngrok_cmd:
        print_colored("WARN", "ngrok is not installed. Webhook testing won't work.", Colors.ERROR)
        print("      Download from: https://ngrok.com/download")
        print("      (Continuing without ngrok...)\n")
    
    def cleanup():
        """Cleanup all processes on exit."""
        print(f"\n{Colors.BOLD}Shutting down...{Colors.RESET}")
        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception as e:
                logging.debug(f"Graceful termination failed: {e}, forcing kill...")
                try:
                    proc.kill()
                except Exception as kill_error:
                    # Process may have already exited - log for debugging
                    logging.debug(f"Kill failed (process may have exited): {kill_error}")
        print("All services stopped.")
    
    # Handle Ctrl+C
    def signal_handler(sig, frame):
        cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 1. Start Backend
        print_colored("BACKEND", "Starting FastAPI server on http://localhost:8080...", Colors.BACKEND)
        
        backend_env = os.environ.copy()
        backend_env["PYTHONPATH"] = str(project_root / "src")
        
        backend_proc = subprocess.Popen(
            [sys.executable, "run_api.py"],
            cwd=project_root,
            env=backend_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(backend_proc)
        
        # Start thread to stream backend output
        backend_thread = threading.Thread(
            target=stream_output,
            args=(backend_proc, "BACKEND", Colors.BACKEND),
            daemon=True
        )
        backend_thread.start()
        
        # Wait for backend to start
        time.sleep(2)
        
        if backend_proc.poll() is not None:
            print_colored("ERROR", "Backend failed to start!", Colors.ERROR)
            cleanup()
            sys.exit(1)
        
        # 2. Start ngrok (if available)
        ngrok_url = None
        if ngrok_cmd:
            print_colored("NGROK", f"Starting ngrok tunnel using: {ngrok_cmd}", Colors.NGROK)
            
            ngrok_proc = subprocess.Popen(
                [ngrok_cmd, "http", "8080", "--log=stdout"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            processes.append(ngrok_proc)
            
            # Start thread for ngrok output
            ngrok_thread = threading.Thread(
                target=stream_output,
                args=(ngrok_proc, "NGROK", Colors.NGROK),
                daemon=True
            )
            ngrok_thread.start()
            
            # Wait for ngrok to provide URL
            print_colored("NGROK", "Waiting for tunnel URL...", Colors.NGROK)
            ngrok_url = find_ngrok_url(ngrok_proc)
            
            if ngrok_url:
                print_colored("NGROK", f"✅ Tunnel URL: {ngrok_url}", Colors.NGROK)
                print_colored("NGROK", f"   Webhook URL: {ngrok_url}/webhook", Colors.NGROK)
            else:
                print_colored("NGROK", "⚠️  Could not get tunnel URL. Check ngrok output.", Colors.NGROK)
        
        # 3. Start Frontend
        print_colored("FRONTEND", "Starting dashboard on http://localhost:5173...", Colors.FRONTEND)
        
        # Get npm path securely
        npm_path = get_npm_path()
        if not npm_path:
            print_colored("ERROR", "npm executable not found in PATH!", Colors.ERROR)
            cleanup()
            sys.exit(1)
        
        # Check if node_modules exists
        if not (dashboard_dir / "node_modules").exists():
            print_colored("FRONTEND", "Installing dependencies (npm install)...", Colors.FRONTEND)
            npm_install = subprocess.run(
                [npm_path, "install"],
                cwd=dashboard_dir,
                capture_output=True
                # shell=False (default) - using resolved npm_path for security
            )
            if npm_install.returncode != 0:
                print_colored("ERROR", "npm install failed!", Colors.ERROR)
                print(npm_install.stderr.decode())
                cleanup()
                sys.exit(1)
        
        frontend_proc = subprocess.Popen(
            [npm_path, "run", "dev"],
            cwd=dashboard_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
            # shell=False (default) - using resolved npm_path for security
        )
        processes.append(frontend_proc)
        
        # Start thread for frontend output
        frontend_thread = threading.Thread(
            target=stream_output,
            args=(frontend_proc, "FRONTEND", Colors.FRONTEND),
            daemon=True
        )
        frontend_thread.start()
        
        # Wait for frontend to start
        time.sleep(3)
        
        # Print summary
        print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}✅ All services started!{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
        
        print(f"  📊 Dashboard:  http://localhost:5173")
        print(f"  🔧 Backend:    http://localhost:8080")
        print(f"  📡 Health:     http://localhost:8080/")
        
        if ngrok_url:
            print(f"\n  🌐 External URL: {ngrok_url}")
            print(f"  🔗 Webhook URL:  {ngrok_url}/webhook")
            print(f"\n  📝 Update GitHub webhook settings with the URL above")
        
        print(f"\n  Press {Colors.BOLD}Ctrl+C{Colors.RESET} to stop all services.\n")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
        
        # Track which processes we've already warned about
        warned_processes = set()
        
        # Critical processes that must keep running
        critical_processes = {"Backend": processes[0], "Frontend": processes[-1]}
        
        # Keep running until interrupted
        while True:
            # Check if critical processes died
            for name, proc in critical_processes.items():
                if proc.poll() is not None and name not in warned_processes:
                    warned_processes.add(name)
                    print_colored("ERROR", f"{name} process died unexpectedly!", Colors.ERROR)
                    cleanup()
                    sys.exit(1)
            
            # Check ngrok (non-critical, warn only once)
            if ngrok_cmd and len(processes) > 1:
                ngrok_proc = processes[1]
                if ngrok_proc.poll() is not None and "ngrok" not in warned_processes:
                    warned_processes.add("ngrok")
                    print_colored("WARN", "ngrok process stopped. Webhook testing won't work.", Colors.ERROR)
                    print("      You can restart ngrok manually: ngrok http 8080")
            
            time.sleep(1)
            
    except Exception as e:
        print_colored("ERROR", f"Failed to start services: {e}", Colors.ERROR)
        cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()
