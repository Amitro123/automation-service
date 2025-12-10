# Dependency Management

This project maintains dependencies in both `pyproject.toml` and `requirements.txt`:

- **`pyproject.toml`**: Source of truth for package installation via `pip install -e .`
- **`requirements.txt`**: Used for direct pip installation and CI/CD environments

## Keeping Dependencies in Sync

When adding or updating dependencies:

1. **Update `pyproject.toml`** first (under `[project.dependencies]`)
2. **Update `requirements.txt`** with matching version constraints
3. **Ensure version specs match** between both files

## Version Pinning Guidelines

- **Production dependencies**: Use `>=` for flexibility (e.g., `flask>=3.0.0`)
- **Critical dependencies**: Pin exact versions if needed (e.g., `anthropic==0.18.1`)
- **Development dependencies**: Listed in `requirements-dev.txt`

## Example

```toml
# pyproject.toml
dependencies = [
    "flask>=3.0.0",
    "openai>=1.40.0",
]
```

```txt
# requirements.txt
flask>=3.0.0
openai>=1.40.0
```

## Future Consideration

Consider migrating to a single source of truth using one of:
- **Option 1**: Use `pip-compile` to generate `requirements.txt` from `pyproject.toml`
- **Option 2**: Reference `requirements.txt` from `pyproject.toml`: `dependencies = {file = ["requirements.txt"]}`
