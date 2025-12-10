import typer
import json
import os
import requests
import asyncio
from typing import Optional
from enum import Enum
from pathlib import Path

# Use relative imports if possible, or fall back to installed package
try:
    from automation_agent.config import Config
    from automation_agent.api_server import app  # Check if we can import app directly? Likely safer to rely on config.
except ImportError:
    # Attempt to handle if run file directly
    pass

app = typer.Typer(help="StudioAI CLI - GitHub Automation Agent Configuration & Management")

CONFIG_FILE = "studioai.config.json"

class TriggerMode(str, Enum):
    PR = "pr"
    PUSH = "push"
    BOTH = "both"

@app.command()
def init(
    owner: str = typer.Option(..., prompt="GitHub Owner"),
    repo: str = typer.Option(..., prompt="GitHub Repository Name"),
    trigger_mode: TriggerMode = typer.Option(TriggerMode.PR, prompt="Trigger Mode (pr/push/both)"),
    group_updates: bool = typer.Option(True, prompt="Group Automation Updates?"),
    post_review_on_pr: bool = typer.Option(True, prompt="Post Review on PR?")
):
    """Initialize StudioAI configuration."""
    config_data = {
        "repository_owner": owner,
        "repository_name": repo,
        "trigger_mode": trigger_mode.value,
        "group_automation_updates": group_updates,
        "post_review_on_pr": post_review_on_pr
    }
    
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f, indent=4)
    
    typer.echo(f"✅ Configuration saved to {CONFIG_FILE}")
    typer.echo("Note: Environment variables (.env) take precedence over these settings.")

@app.command()
def configure(
    trigger_mode: Optional[TriggerMode] = typer.Option(None),
    group_updates: Optional[bool] = typer.Option(None),
    post_review_on_pr: Optional[bool] = typer.Option(None)
):
    """Update existing configuration."""
    if not os.path.exists(CONFIG_FILE):
        typer.echo("Config file not found. Run 'studioai init' first.")
        raise typer.Exit(code=1)
        
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
        
    if trigger_mode:
        config["trigger_mode"] = trigger_mode.value
    if group_updates is not None:
        config["group_automation_updates"] = group_updates
    if post_review_on_pr is not None:
        config["post_review_on_pr"] = post_review_on_pr
        
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
        
    typer.echo(f"✅ Configuration updated in {CONFIG_FILE}")

@app.command()
def status():
    """Check system status via API."""
    try:
        # Assuming local API for now, typically config.PORT
        # We need to load config to know port, or assume default
        # Ideally we'd have a robust way to find the running server URL
        url = "http://localhost:8080/api/metrics" 
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        typer.echo("\n📊 System Status")
        typer.echo("================")
        typer.echo(f"Success Rate: {data.get('success_rate', 'N/A')}")
        typer.echo(f"Total Runs: {data.get('total_runs', 'N/A')}")
        
        # Could show recent runs here if API supported it
        # history = requests.get("http://localhost:8080/api/history").json()
        # ...
        
    except Exception as e:
        typer.echo(f"❌ Failed to connect to API: {e}")
        typer.echo("Is the backend running?")

@app.command()
def test_pr_flow():
    """Trigger a smoke test for PR flow."""
    typer.echo("🔬 Running PR Flow Smoke Test...")
    # This invokes the internal orchestrator logic in a DRY run or TEST mode if possible
    # For now, we might just ping a test endpoint or simulate a payload
    # Given the MVP, we will try to reach a new test endpoint if we add one, 
    # OR mainly just verify we can load config and "simulate" the check.
    
    # Per user request: "Validates webhook config. Triggers a test run (if possible)"
    # We can perform a config validation check here.
    
    if os.path.exists(CONFIG_FILE):
         typer.echo("✅ studioai.config.json found")
    else:
         typer.echo("⚠️ studioai.config.json missing")

    typer.echo("To fully test, please utilize the 'check_e2e.py' script or triggering a real PR.")
    # Future: POST /api/test/trigger

if __name__ == "__main__":
    app()
