"""Demonstration script for Story 28.2: Enhanced Workflow Selector with Ceremony Injection.

This script demonstrates how ceremonies are automatically injected into workflow sequences
based on scale level.
"""

from gao_dev.methodologies.adaptive_agile.workflow_selector import WorkflowSelector
from gao_dev.methodologies.adaptive_agile.scale_levels import ScaleLevel


def print_workflows(scale_level: ScaleLevel, workflows):
    """Print workflow list with ceremonies highlighted."""
    print(f"\n{'='*80}")
    print(f"Scale Level: {scale_level.name} (Level {scale_level.value})")
    print(f"{'='*80}")
    print(f"Total workflows: {len(workflows)}")
    print()

    ceremonies = []
    regular = []

    for i, workflow in enumerate(workflows, 1):
        if "ceremony" in workflow.workflow_name:
            ceremonies.append(workflow)
            marker = " [CEREMONY]"
        else:
            regular.append(workflow)
            marker = ""

        print(f"{i:2}. {workflow.workflow_name:30} "
              f"phase={workflow.phase:15} "
              f"required={str(workflow.required):5} "
              f"depends_on={workflow.depends_on}{marker}")

    print()
    print(f"Regular workflows: {len(regular)}")
    print(f"Ceremony workflows: {len(ceremonies)}")

    if ceremonies:
        print("\nCeremonies injected:")
        for ceremony in ceremonies:
            print(f"  - {ceremony.workflow_name} (after {', '.join(ceremony.depends_on)})")


def main():
    """Run demonstration."""
    print("\n" + "="*80)
    print("Story 28.2: Enhanced Workflow Selector with Ceremony Injection")
    print("Demonstration of automatic ceremony injection based on scale level")
    print("="*80)

    selector = WorkflowSelector()

    # Test each scale level
    for scale_level in [
        ScaleLevel.LEVEL_0_CHORE,
        ScaleLevel.LEVEL_1_BUG_FIX,
        ScaleLevel.LEVEL_2_SMALL_FEATURE,
        ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        ScaleLevel.LEVEL_4_GREENFIELD
    ]:
        workflows = selector.select_workflows(scale_level)
        print_workflows(scale_level, workflows)

    print("\n" + "="*80)
    print("Demonstration complete!")
    print("="*80)
    print("\nKey Observations:")
    print("  - Level 0: No ceremonies (direct implementation)")
    print("  - Level 1: Retrospective only (on repeated failure)")
    print("  - Level 2: Standup + Retrospective (planning optional)")
    print("  - Level 3: Planning + Standup + Retrospective (all present)")
    print("  - Level 4: Planning + Standup + Retrospective (comprehensive)")
    print()


if __name__ == "__main__":
    main()
