"""
Epic 6 Regression Test Suite.

CRITICAL: These tests MUST pass before and after Epic 6 refactoring.

Purpose:
- Capture current behavior of GAODevOrchestrator (1,327 lines)
- Capture current behavior of SandboxManager (781 lines)
- Verify zero regressions after service extraction
- Establish performance baselines

Usage:
    # Before Epic 6: Capture baseline
    pytest tests/regression/epic_6/ -v --baseline-mode=capture

    # After each story: Validate
    pytest tests/regression/epic_6/ -v

    # Compare performance
    pytest tests/regression/epic_6/test_performance_baseline.py --baseline-mode=compare
"""
