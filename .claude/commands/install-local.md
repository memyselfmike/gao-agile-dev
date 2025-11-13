# Install GAO-Dev Locally

Install the GAO-Dev package locally in editable mode for development and testing.

## Instructions

1. Run the install script: `bash scripts/install_local.sh`
2. Show the user:
   - Installation status
   - Installed version (from `gao-dev --version`)
   - Confirmation that CLI commands are available

## Notes

- Installs in editable mode with `pip install -e .`
- Includes all dependencies from pyproject.toml
- Useful for local development and testing before release
- Version will be derived from git tags via setuptools-scm
