# Pre-Release Checks

Run comprehensive pre-release checks to ensure code quality before creating a release.

## Instructions

1. Run the pre-release check script: `bash scripts/pre_release_check.sh`
2. Show the user the results of each check:
   - Tests (pytest with coverage)
   - Type checking (mypy)
   - Code formatting (black)
   - Linting (ruff)
   - Git status (uncommitted changes)
   - Version detection (setuptools-scm)
   - Build validation (wheel creation)

## Notes

- All checks must pass before release
- Script exits on first failure for fast feedback
- Covers all quality gates from CI pipeline
- Use before manually triggering beta release workflow
