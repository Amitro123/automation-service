import sys
import os
sys.path.append(os.path.join(os.getcwd(), "src"))

try:
    from automation_agent.code_reviewer import CodeReviewer
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")
