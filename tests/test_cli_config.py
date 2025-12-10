import os
import json
import pytest
from unittest.mock import patch, mock_open
from automation_agent.config import Config
from typer.testing import CliRunner
from automation_agent.cli import app, CONFIG_FILE

runner = CliRunner()

@pytest.fixture
def clean_config():
    """Remove config file and env vars before test."""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    
    # Reset internal config state
    Config._file_config = {}
    
    # Unset env vars that might interfere
    old_env = dict(os.environ)
    for key in ["TRIGGER_MODE", "GROUP_AUTOMATION_UPDATES", "POST_REVIEW_ON_PR"]:
        if key in os.environ:
            del os.environ[key]
            
    yield
    
    # Restore
    os.environ.clear()
    os.environ.update(old_env)
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)

def test_cli_init_writes_file(clean_config):
    """Test that 'studioai init' creates a valid config file."""
    # Use arguments to avoid prompt issues
    result = runner.invoke(app, [
        "init", 
        "--owner", "myowner", 
        "--repo", "myrepo", 
        "--trigger-mode", "pr", 
        "--group-updates", # Flag sets it to True
        "--post-review-on-pr" # Flag sets it to True
    ])
    
    if result.exit_code != 0:
        print(f"Init command failed: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")

    assert result.exit_code == 0
    assert "Configuration saved" in result.stdout
    assert os.path.exists(CONFIG_FILE)
    
    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)
        assert data["repository_owner"] == "myowner"
        assert data["repository_name"] == "myrepo"
        assert data["trigger_mode"] == "pr"
        assert data["group_automation_updates"] is True

def test_cli_configure_updates_file(clean_config):
    """Test that 'studioai configure' updates existing file."""
    # Create initial file
    initial = {"trigger_mode": "push", "group_automation_updates": False}
    with open(CONFIG_FILE, "w") as f:
        json.dump(initial, f)
        
    # Use flag for boolean (presence = True)
    result = runner.invoke(app, ["configure", "--trigger-mode", "both", "--group-updates"])
    
    if result.exit_code != 0:
        print(f"Configure command failed: {result.output}")
        
    assert result.exit_code == 0
    
    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)
        assert data["trigger_mode"] == "both"
        assert data["group_automation_updates"] is True

def test_config_precedence(clean_config):
    """Test Env > File > Default precedence."""
    
    # 1. Default (when no env and no file)
    assert Config.TRIGGER_MODE == "both"  # Default in class
    
    # 2. File should override Default
    with open(CONFIG_FILE, "w") as f:
        json.dump({"trigger_mode": "pr"}, f)
    
    Config.load() # Reload
    assert Config.TRIGGER_MODE == "pr"
    
    # 3. Env should override File
    os.environ["TRIGGER_MODE"] = "push"
    assert Config.TRIGGER_MODE == "push"
