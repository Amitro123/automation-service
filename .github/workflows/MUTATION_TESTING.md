# Mutation Testing CI Workflow

This workflow runs mutation tests on Linux (ubuntu-latest) and saves results as artifacts.

## Triggers

- **Push to main branch**: Automatically runs mutation tests
- **Manual trigger**: Via GitHub Actions UI (workflow_dispatch)
- **Pull requests** (optional): Uncomment the `pull_request` section to enable

## What it does

1. **Setup**: Installs Python 3.11, dependencies from `requirements.txt` and `requirements-dev.txt`
2. **Coverage**: Runs `pytest --cov` to generate coverage.xml
3. **Mutation Tests**: Runs mutation tests using `mutation_service.py`
4. **Artifacts**: Uploads `mutation_results.json` and `coverage.xml` (30 day retention)
5. **Summary**: Displays mutation score in GitHub Actions summary
6. **PR Comments**: Automatically comments on PRs with mutation test results (if enabled)

## Results

After the workflow runs:
- Download `mutation_results.json` from workflow artifacts
- Copy it to your local repo root
- Restart the dashboard API server
- Dashboard will display the real mutation score from CI

## Configuration

The workflow uses:
- `PYTHONPATH` to import mutation_service
- 600 second (10 minute) timeout for mutation tests
- Continues even if pytest fails (to still run mutations)

## Enabling PR Comments

Uncomment the `pull_request` trigger to:
- Run mutation tests on every PR
- Auto-comment results on the PR
- Help reviewers see test quality metrics

## Manual Trigger

1. Go to Actions tab in GitHub
2. Select "Mutation Testing" workflow
3. Click "Run workflow"
4. Select branch and run

## Viewing Results

**In GitHub Actions:**
- Check the workflow summary for mutation score
- Download artifacts to see full results

**In Dashboard:**
- Copy `mutation_results.json` from artifacts to repo root
- Restart API server
- Dashboard shows real mutation score

## Notes

- Mutation tests only run on Linux (mutmut requirement)
- Tests can take 5-10 minutes depending on codebase size
- Results are cached for 30 days
- Workflow is disabled by default on feature branches (only main)
