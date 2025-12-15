#!/usr/bin/env python
"""Run the FastAPI server for GitHub Automation Agent."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from automation_agent.main_api import main

if __name__ == "__main__":
    main()
