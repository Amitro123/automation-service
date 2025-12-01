import os
import json
import pytest
from src.automation_agent.session_memory import SessionMemoryStore

TEST_DB = "test_session_memory.json"

@pytest.fixture
def store():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    store = SessionMemoryStore(storage_path=TEST_DB)
    yield store
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_add_run(store):
    run = store.add_run("run1", "sha123", "main")
    assert run["id"] == "run1"
    assert run["status"] == "running"
    assert len(store.get_history()) == 1

def test_update_run_status(store):
    store.add_run("run1", "sha123", "main")
    store.update_run_status("run1", "completed", "All good")
    run = store.get_run("run1")
    assert run["status"] == "completed"
    assert run["summary"] == "All good"
    assert "end_time" in run

def test_update_task_result(store):
    store.add_run("run1", "sha123", "main")
    store.update_task_result("run1", "code_review", {"success": True})
    run = store.get_run("run1")
    assert run["tasks"]["code_review"]["success"] is True

def test_metrics(store):
    store.add_run("run1", "sha123", "main")
    store.add_metric("run1", "tokens_used", 100)
    store.add_metric("run1", "estimated_cost", 0.05)
    
    run = store.get_run("run1")
    assert run["metrics"]["tokens_used"] == 100
    
    global_metrics = store.get_global_metrics()
    assert global_metrics["total_tokens"] == 100
    assert global_metrics["total_cost"] == 0.05

def test_persistence():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    # Create and save
    store1 = SessionMemoryStore(storage_path=TEST_DB)
    store1.add_run("run1", "sha123", "main")
    
    # Load new instance
    store2 = SessionMemoryStore(storage_path=TEST_DB)
    history = store2.get_history()
    assert len(history) == 1
    assert history[0]["id"] == "run1"
    
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
