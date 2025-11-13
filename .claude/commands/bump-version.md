# Bump Version

Calculate and display the next version based on conventional commits or manual bump type.

## Instructions

Ask the user which bump type they want (or use auto-detection):
- **auto**: Automatically detect from conventional commits (BREAKING CHANGE -> major, feat -> minor, fix -> patch)
- **major**: Breaking changes (e.g., 1.0.0 -> 2.0.0)
- **minor**: New features (e.g., 1.0.0 -> 1.1.0)
- **patch**: Bug fixes (e.g., 1.0.0 -> 1.0.1)

Then run the appropriate command:

### Auto-detection (recommended):
```bash
python scripts/bump_version.py
```

### Manual bump:
```bash
python scripts/bump_version.py <current_version> <bump_type>
# Example: python scripts/bump_version.py 0.1.0 minor
```

Show the user:
1. Current version (from latest git tag)
2. Next version based on commits or bump type
3. Commits analyzed (if auto mode)
4. Suggested next steps

## Notes

- Auto mode analyzes commits since last tag
- Looks for: BREAKING CHANGE (major), feat: (minor), fix: (patch)
- Does NOT create tags (that's done by beta-release workflow)
- Just shows what the next version would be
