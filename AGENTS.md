# Agent Instructions

This document provides instructions for AI agents working on this codebase.

## Project Structure

The project is a Python package located in `src/automation_agent`.

-   `src/automation_agent/`: Core package code.
-   `tests/`: Test directory (needs to be populated).
-   `main.py`: Entry point (moved to `src/automation_agent/main.py`).

## Coding Standards

-   **Style**: Follow PEP 8 guidelines.
-   **Docstrings**: Use Google-style docstrings for all functions and classes.
-   **Type Hinting**: Use Python type hints for all function arguments and return values.
-   **Logging**: Use the `logging` module for all output, not `print`.

## Testing

-   Use `pytest` for testing.
-   Mock external services (`GitHubClient`, `LLMClient`, `requests`) in tests.
-   Do not make real API calls during tests.
-   Aim for high test coverage.

## Workflow

1.  **Read `spec.md`**: Understand the current state and tasks.
2.  **Verify**: Always verify changes by running the code or tests.
3.  **Config**: Use `config.py` for all configuration. Do not hardcode values.
4.  **Dependencies**: Add new dependencies to `requirements.txt`.

## Running the Application

To run the application locally:

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python -m automation_agent.main
```

Ensure environment variables are set (see `.env.example`).
