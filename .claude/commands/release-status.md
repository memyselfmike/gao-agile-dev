# Check Release Status

Check the current release status and provide update instructions for beta testers.

## Instructions

1. **Get current version and recent releases:**
   ```bash
   git describe --tags --abbrev=0
   gh release list --limit=5
   ```

2. **Check recent workflow runs:**
   ```bash
   gh run list --workflow=beta-release.yml --limit=3
   ```

3. **Check commits since last release:**
   ```bash
   git log $(git describe --tags --abbrev=0)..HEAD --oneline
   ```

4. **Format response for user with:**
   - Current version
   - Recent releases
   - Workflow status
   - Install command for latest release

## Output Format

Provide a summary like:

```
**Release Status**

Current Version: v0.2.1-beta.1
Last Release: 2025-11-19

Recent Releases:
- v0.2.1-beta.1 (latest)
- v0.2.0-beta.1
- v0.1.0-beta.1

Workflow Status: [success/failed/pending]

**For Beta Testers:**
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@v0.2.1-beta.1
```

## Notes

- If there are unreleased commits with feat:/fix:, suggest pushing to trigger a release
- If workflow failed, check logs with `gh run view <ID> --log`
- Always provide the exact pip install command for testers
