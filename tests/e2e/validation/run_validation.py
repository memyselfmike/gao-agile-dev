"""Executable script to run POC validation.

This script:
1. Validates environment (ollama, Claude API key)
2. Runs validation comparing Claude and deepseek-r1
3. Generates and saves validation report

Usage:
    python tests/e2e/validation/run_validation.py

Epic: 37 - UX Quality Analysis
Story: 37.0 - deepseek-r1 Quality Validation POC
"""

import asyncio
import sys
import os
from pathlib import Path
import structlog

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.e2e.validation.poc_validator import POCValidator
from tests.e2e.validation.sample_conversations import SAMPLE_CONVERSATIONS

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False
)

logger = structlog.get_logger()


def validate_environment() -> bool:
    """
    Validate required environment is available.

    Returns:
        True if environment is valid, False otherwise
    """
    errors = []

    # Check Claude API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        errors.append("ANTHROPIC_API_KEY environment variable not set")

    # Check ollama (basic check - actual model check happens in validation)
    # We'll let the validation process handle model availability

    if errors:
        logger.error("environment_validation_failed", errors=errors)
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return False

    logger.info("environment_validation_passed")
    return True


async def main() -> int:
    """
    Main execution function.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("=" * 80)
    print("deepseek-r1 QUALITY VALIDATION POC")
    print("=" * 80)
    print()

    # Validate environment
    print("Validating environment...")
    if not validate_environment():
        return 1

    print(f"Environment validated successfully")
    print()

    # Create validator
    print(f"Initializing validator...")
    validator = POCValidator(project_root=project_root)
    print(f"Will analyze {len(SAMPLE_CONVERSATIONS)} conversations")
    print()

    try:
        # Run validation
        print("=" * 80)
        print("PHASE 1: Analyzing with Claude (Ground Truth)")
        print("=" * 80)
        print()
        print("This may take 2-5 minutes depending on API response times...")
        print()

        result = await validator.run_validation()

        print()
        print("=" * 80)
        print("VALIDATION COMPLETE")
        print("=" * 80)
        print()

        # Generate report
        report_text = validator.generate_report(result)

        # Print to console
        print(report_text)

        # Save to file
        report_path = project_root / "docs" / "features" / "e2e-testing-ux-quality" / "POC_VALIDATION_REPORT.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_text)

        print()
        print(f"Report saved to: {report_path}")
        print()

        # Summary
        stats = result.get_summary_stats()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Decision: {stats['decision']}")
        print(f"Score Agreement: {stats['score_agreement_pct']}%")
        print(f"Issue Detection: {stats['issue_detection_recall']}%")
        print(f"Recommendation: {stats['recommendation']}")
        print()

        # Exit code based on decision
        if result.decision == "PASS":
            print("STATUS: PASS - Proceed with deepseek-r1")
            return 0
        elif result.decision == "PARTIAL PASS":
            print("STATUS: PARTIAL PASS - Consider hybrid approach")
            return 0  # Still success, but with caveat
        else:
            print("STATUS: FAIL - Reconsider approach")
            return 1

    except Exception as e:
        logger.error("validation_failed", error=str(e), exc_info=True)
        print()
        print(f"ERROR: Validation failed: {e}", file=sys.stderr)
        print()
        print("Troubleshooting:")
        print("1. Ensure ANTHROPIC_API_KEY is set")
        print("2. Ensure ollama is running: ollama serve")
        print("3. Ensure deepseek-r1 model is available: ollama pull deepseek-r1")
        print("4. Check logs above for specific errors")
        return 1


if __name__ == "__main__":
    import logging
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
