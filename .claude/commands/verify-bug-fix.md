# Verify Bug Fix

Run complete bug fix verification workflow across development and beta environments.

## Instructions

**This command invokes the bug-tester agent with the bug-verification workflow.**

When you run this command, provide:
1. Bug/issue number or description
2. Commit hash where fix was implemented (if known)
3. Files that were changed

The bug-tester agent will:

### Phase 1: Development Environment (CWD)
1. Verify fix in local editable install
2. Run unit and integration tests
3. Use Playwright to test UI
4. Check server logs
5. Verify no console errors
6. Ensure regression test exists

### Phase 2: Beta Environment (C:/Testing)
1. Install latest version from GitHub
2. Verify in beta test environment
3. Test onboarding (if applicable)
4. Test core workflows
5. Check for regressions
6. Compare behavior with dev environment

### Phase 3: Reporting
1. Create comprehensive verification report
2. Document all test results
3. Capture screenshots
4. Update issue tracker
5. Provide release recommendation

## Example Usage

```
/verify-bug-fix

Bug: #123 - Onboarding wizard crashes on step 2
Fixed in: da8505c
Files: gao_dev/web/api/onboarding.py, gao_dev/web/frontend/src/components/OnboardingWizard.tsx
```

## What to Expect

The agent will:
1. ✅ Test in development environment (C:\Projects\gao-agile-dev)
2. ✅ Test in beta environment (C:\Testing)
3. ✅ Run Playwright UI tests
4. ✅ Monitor server logs
5. ✅ Check for regressions
6. ✅ Create verification report
7. ✅ Provide screenshots
8. ✅ Give release recommendation

## Output

You'll receive:
- Verification report in markdown format
- Screenshots showing before/after states
- Test results from both environments
- Server log analysis
- Regression test verification
- Release readiness assessment

## Prerequisites

Before running this command:
- [ ] Fix is implemented and committed
- [ ] Code is pushed to GitHub main branch
- [ ] Unit tests are passing locally
- [ ] C:/Testing environment exists
- [ ] Beta venv is set up

If C:/Testing doesn't exist, see `docs/LOCAL_BETA_TESTING_GUIDE.md` for setup.

## Notes

- This is a comprehensive verification workflow
- Takes 10-20 minutes depending on test complexity
- Requires both development and beta environments
- Produces detailed verification report
- Ensures fix is ready for release to beta testers

## Related Commands

- `/release-status` - Check current release status
- `/beta-release` - Create a new beta release
- `/pre-release-check` - Run pre-release validation checklist
