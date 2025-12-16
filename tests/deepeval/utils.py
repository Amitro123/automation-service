
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import os
import google.generativeai as genai
from deepeval.models.base_model import DeepEvalBaseLLM
from dotenv import load_dotenv

load_dotenv()


class DeepEvalGemini(DeepEvalBaseLLM):
    """Wrapper for Google Gemini to be used as a judge in DeepEval."""
    def __init__(self, model_name="gemini-2.5-flash"):
        self.model_name = model_name
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error running Gemini: {e}"

    async def a_generate(self, prompt: str) -> str:
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            return f"Error running Gemini: {e}"

    def get_model_name(self):
        return self.model_name

# Mock SessionMemory for testing without database
class MockSessionMemory:
    def __init__(self):
        self.runs = {}
        
    def create_run(self) -> str:
        run_id = str(uuid.uuid4())
        self.runs[run_id] = {
            "id": run_id,
            "status": "running",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "logs": [],
            "artifacts": {}
        }
        return run_id
        
    def update_run_status(self, run_id: str, status: str, summary: Optional[str] = None):
        if run_id in self.runs:
            self.runs[run_id]["status"] = status
            if summary:
                self.runs[run_id]["summary"] = summary
                
    def add_log(self, run_id: str, level: str, message: str):
        if run_id in self.runs:
            self.runs[run_id]["logs"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": level,
                "message": message
            })

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        return self.runs.get(run_id)

def create_synthetic_diff(filename: str, original: str, modified: str) -> str:
    """Helper to create a unified diff string for testing."""
    return f"""diff --git a/{filename} b/{filename}
index 1234567..89abcdef 100644
--- a/{filename}
+++ b/{filename}
@@ -1,3 +1,3 @@
-{original}
+{modified}
"""
