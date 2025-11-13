# Generate Changelog

Generate or update the CHANGELOG.md file using git-cliff.

## Prerequisites

Check that git-cliff is installed:
```bash
git cliff --version
```

If not installed:
- **macOS**: `brew install git-cliff`
- **Linux**: Download from https://github.com/orhun/git-cliff/releases
- **Windows**: `cargo install git-cliff` or download binary

## Instructions

### Preview changelog (without writing):
```bash
git cliff --unreleased
```

### Update CHANGELOG.md with latest changes:
```bash
git cliff --tag v0.1.0 --output CHANGELOG.md
```
(Replace `v0.1.0` with the next version tag)

### Generate for a specific range:
```bash
git cliff v0.1.0..HEAD --output CHANGELOG.md
```

### Generate full changelog from all tags:
```bash
git cliff --output CHANGELOG.md
```

## Show the user:
1. Preview of generated changelog
2. Commit types detected (feat, fix, docs, etc.)
3. Breaking changes (if any)
4. Whether CHANGELOG.md was updated

## Notes

- Configuration in `.cliff.toml`
- Uses conventional commits format
- Groups commits by type (Features, Bug Fixes, Documentation, etc.)
- Detects breaking changes
- Automatically run by beta-release workflow
- Can be run manually for preview
