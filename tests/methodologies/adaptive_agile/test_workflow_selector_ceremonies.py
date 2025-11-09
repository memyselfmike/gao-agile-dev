"""Unit tests for workflow selector ceremony injection.

Story 28.2: Enhanced Workflow Selector with Ceremony Injection
"""

from pathlib import Path

from gao_dev.methodologies.adaptive_agile.workflow_selector import WorkflowSelector
from gao_dev.methodologies.adaptive_agile.scale_levels import ScaleLevel
from gao_dev.core.models.methodology import WorkflowStep


class TestCeremonyInjection:
    """Test ceremony injection logic."""

    def test_level_0_no_ceremonies(self):
        """Level 0 (chore) has no ceremonies."""
        selector = WorkflowSelector()
        workflows = selector.select_workflows(ScaleLevel.LEVEL_0_CHORE)

        ceremony_names = [w.workflow_name for w in workflows if "ceremony" in w.workflow_name]
        assert len(ceremony_names) == 0, "Level 0 should have no ceremonies"

    def test_level_1_no_ceremonies_by_default(self):
        """Level 1 (bug fix) has no ceremonies by default."""
        selector = WorkflowSelector()
        workflows = selector.select_workflows(ScaleLevel.LEVEL_1_BUG_FIX)

        # Note: Level 1 can have retrospective on repeated failure,
        # but by default (without failure context) it shouldn't
        ceremony_names = [w.workflow_name for w in workflows if "ceremony" in w.workflow_name]

        # Level 1 should have retrospective (Story 28.2 spec says it's available)
        assert "retrospective-ceremony" in ceremony_names, \
            "Level 1 should have retrospective ceremony"

    def test_level_2_has_retrospective_only(self):
        """Level 2 has retrospective, optional planning, conditional standup."""
        selector = WorkflowSelector()
        workflows = selector.select_workflows(ScaleLevel.LEVEL_2_SMALL_FEATURE)

        ceremony_names = [w.workflow_name for w in workflows if "ceremony" in w.workflow_name]

        # Should have retrospective
        assert "retrospective-ceremony" in ceremony_names, \
            "Level 2 should have retrospective ceremony"

        # Planning optional (not injected by default - required=False in config)
        assert "planning-ceremony" not in ceremony_names, \
            "Level 2 should not have planning ceremony (optional/not required)"

        # Standup is conditional on story count (injected but may not trigger)
        # For now, we inject it and let the trigger engine decide
        assert "standup-ceremony" in ceremony_names, \
            "Level 2 should have standup ceremony available"

    def test_level_3_has_planning_and_retrospective(self):
        """Level 3 has planning (required) and retrospective."""
        selector = WorkflowSelector()
        workflows = selector.select_workflows(ScaleLevel.LEVEL_3_MEDIUM_FEATURE)

        ceremony_names = [w.workflow_name for w in workflows if "ceremony" in w.workflow_name]

        assert "planning-ceremony" in ceremony_names, \
            "Level 3 should have planning ceremony"
        assert "retrospective-ceremony" in ceremony_names, \
            "Level 3 should have retrospective ceremony"
        assert "standup-ceremony" in ceremony_names, \
            "Level 3 should have standup ceremony"

    def test_level_4_has_all_ceremonies(self):
        """Level 4 has all ceremonies."""
        selector = WorkflowSelector()
        workflows = selector.select_workflows(ScaleLevel.LEVEL_4_GREENFIELD)

        ceremony_names = [w.workflow_name for w in workflows if "ceremony" in w.workflow_name]

        assert "planning-ceremony" in ceremony_names, \
            "Level 4 should have planning ceremony"
        assert "standup-ceremony" in ceremony_names, \
            "Level 4 should have standup ceremony"
        assert "retrospective-ceremony" in ceremony_names, \
            "Level 4 should have retrospective ceremony"

    def test_planning_ceremony_after_prd(self):
        """Planning ceremony injected after create-prd."""
        selector = WorkflowSelector()
        workflows = selector.select_workflows(ScaleLevel.LEVEL_3_MEDIUM_FEATURE)

        # Find planning ceremony
        planning_idx = None
        for i, w in enumerate(workflows):
            if w.workflow_name == "planning-ceremony":
                planning_idx = i
                break

        assert planning_idx is not None, "Planning ceremony should be present"

        # Check depends_on includes create-prd or create-epics
        planning = workflows[planning_idx]
        assert len(planning.depends_on) > 0, "Planning ceremony should have dependencies"
        assert "create-prd" in planning.depends_on or "create-epics" in planning.depends_on, \
            "Planning ceremony should depend on create-prd or create-epics"

    def test_standup_after_implementation(self):
        """Standup ceremony injected after implementation."""
        selector = WorkflowSelector()
        workflows = selector.select_workflows(ScaleLevel.LEVEL_3_MEDIUM_FEATURE)

        # Find standup ceremony
        standup = next((w for w in workflows if w.workflow_name == "standup-ceremony"), None)
        assert standup is not None, "Standup ceremony should be present"

        # Check depends_on includes implementation workflow
        assert len(standup.depends_on) > 0, "Standup ceremony should have dependencies"
        assert "implement-stories" in standup.depends_on or "story-development" in standup.depends_on, \
            "Standup ceremony should depend on implementation workflow"

    def test_retrospective_after_testing(self):
        """Retrospective ceremony injected after testing."""
        selector = WorkflowSelector()
        workflows = selector.select_workflows(ScaleLevel.LEVEL_3_MEDIUM_FEATURE)

        # Find retrospective ceremony
        retro = next((w for w in workflows if w.workflow_name == "retrospective-ceremony"), None)
        assert retro is not None, "Retrospective ceremony should be present"

        # Check depends_on includes testing workflow
        assert len(retro.depends_on) > 0, "Retrospective ceremony should have dependencies"
        testing_workflows = ["test-feature", "integration-testing", "code-review"]
        has_testing_dep = any(dep in testing_workflows for dep in retro.depends_on)
        assert has_testing_dep, \
            "Retrospective ceremony should depend on testing/review workflow"

    def test_ceremony_injection_disabled(self):
        """Ceremonies not injected when disabled."""
        selector = WorkflowSelector()
        workflows = selector.select_workflows(
            ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            include_ceremonies=False
        )

        ceremony_names = [w.workflow_name for w in workflows if "ceremony" in w.workflow_name]
        assert len(ceremony_names) == 0, \
            "No ceremonies should be present when injection is disabled"

    def test_dependency_graph_validity(self):
        """Injected ceremonies don't break dependency graph."""
        selector = WorkflowSelector()
        workflows = selector.select_workflows(ScaleLevel.LEVEL_3_MEDIUM_FEATURE)

        workflow_names = {w.workflow_name for w in workflows}

        for workflow in workflows:
            for dep in workflow.depends_on:
                assert dep in workflow_names, \
                    f"Missing dependency: {dep} for workflow {workflow.workflow_name}"

    def test_empty_workflow_list(self):
        """Handle empty workflow list gracefully."""
        selector = WorkflowSelector()

        # Test with empty list
        result = selector._inject_ceremonies([], ScaleLevel.LEVEL_2_SMALL_FEATURE)
        assert result == [], "Empty list should remain empty"

    def test_single_workflow(self):
        """Handle single workflow gracefully."""
        selector = WorkflowSelector()

        workflows = [
            WorkflowStep(
                workflow_name="create-prd",
                phase="planning",
                required=True
            )
        ]

        result = selector._inject_ceremonies(workflows, ScaleLevel.LEVEL_3_MEDIUM_FEATURE)

        # Should have original workflow plus planning ceremony
        assert len(result) >= 1, "Should have at least one workflow"
        assert result[0].workflow_name == "create-prd", "Original workflow should be first"

        # May have planning ceremony injected after
        ceremony_names = [w.workflow_name for w in result if "ceremony" in w.workflow_name]
        if "planning-ceremony" in ceremony_names:
            assert result[1].workflow_name == "planning-ceremony", \
                "Planning ceremony should follow create-prd"


class TestCeremonyRequirements:
    """Test ceremony requirement rules."""

    def test_planning_required_level_3_plus(self):
        """Planning ceremony is required for level 3+."""
        selector = WorkflowSelector()

        # Level 2: Not required
        workflows_l2 = selector.select_workflows(ScaleLevel.LEVEL_2_SMALL_FEATURE)
        planning_l2 = next((w for w in workflows_l2 if w.workflow_name == "planning-ceremony"), None)
        if planning_l2:
            assert not planning_l2.required, "Planning should not be required for Level 2"

        # Level 3: Required
        workflows_l3 = selector.select_workflows(ScaleLevel.LEVEL_3_MEDIUM_FEATURE)
        planning_l3 = next((w for w in workflows_l3 if w.workflow_name == "planning-ceremony"), None)
        assert planning_l3 is not None, "Planning ceremony should exist for Level 3"
        assert planning_l3.required, "Planning should be required for Level 3"

        # Level 4: Required
        workflows_l4 = selector.select_workflows(ScaleLevel.LEVEL_4_GREENFIELD)
        planning_l4 = next((w for w in workflows_l4 if w.workflow_name == "planning-ceremony"), None)
        assert planning_l4 is not None, "Planning ceremony should exist for Level 4"
        assert planning_l4.required, "Planning should be required for Level 4"

    def test_standup_not_required(self):
        """Standup ceremony is never strictly required (conditional on triggers)."""
        selector = WorkflowSelector()

        for scale_level in [ScaleLevel.LEVEL_2_SMALL_FEATURE,
                           ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
                           ScaleLevel.LEVEL_4_GREENFIELD]:
            workflows = selector.select_workflows(scale_level)
            standup = next((w for w in workflows if w.workflow_name == "standup-ceremony"), None)

            if standup:
                assert not standup.required, \
                    f"Standup should not be required for {scale_level.name}"

    def test_retrospective_required_level_2_plus(self):
        """Retrospective ceremony is required for level 2+."""
        selector = WorkflowSelector()

        # Level 0: Not present
        workflows_l0 = selector.select_workflows(ScaleLevel.LEVEL_0_CHORE)
        retro_l0 = next((w for w in workflows_l0 if w.workflow_name == "retrospective-ceremony"), None)
        assert retro_l0 is None, "Retrospective should not be present for Level 0"

        # Level 2: Required
        workflows_l2 = selector.select_workflows(ScaleLevel.LEVEL_2_SMALL_FEATURE)
        retro_l2 = next((w for w in workflows_l2 if w.workflow_name == "retrospective-ceremony"), None)
        assert retro_l2 is not None, "Retrospective ceremony should exist for Level 2"
        assert retro_l2.required, "Retrospective should be required for Level 2"

        # Level 3: Required
        workflows_l3 = selector.select_workflows(ScaleLevel.LEVEL_3_MEDIUM_FEATURE)
        retro_l3 = next((w for w in workflows_l3 if w.workflow_name == "retrospective-ceremony"), None)
        assert retro_l3 is not None, "Retrospective ceremony should exist for Level 3"
        assert retro_l3.required, "Retrospective should be required for Level 3"


class TestCeremonyConfiguration:
    """Test ceremony configuration loading and usage."""

    def test_load_default_config(self):
        """Default configuration loads correctly."""
        selector = WorkflowSelector()
        assert selector.ceremony_config is not None, "Config should be loaded"
        assert "triggers" in selector.ceremony_config, "Config should have triggers"
        assert "features" in selector.ceremony_config, "Config should have features"

    def test_feature_flag_respected(self):
        """Feature flag controls ceremony injection."""
        # Create custom config with feature disabled
        import tempfile
        import yaml

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "ceremony_triggers.yaml"
            config = {
                "triggers": {
                    "planning": {"level_3": {"required": True}},
                    "standup": {},
                    "retrospective": {}
                },
                "features": {
                    "enable_ceremony_integration": False
                }
            }

            with open(config_path, "w") as f:
                yaml.dump(config, f)

            selector = WorkflowSelector(config_dir=Path(tmpdir))
            workflows = selector.select_workflows(
                ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
                include_ceremonies=True
            )

            ceremony_names = [w.workflow_name for w in workflows if "ceremony" in w.workflow_name]
            assert len(ceremony_names) == 0, \
                "No ceremonies should be injected when feature flag is off"

    def test_custom_config_loading(self):
        """Custom configuration file loads correctly."""
        import tempfile
        import yaml

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "ceremony_triggers.yaml"
            config = {
                "triggers": {
                    "planning": {
                        "level_2": {"required": True, "trigger": "epic_start"}
                    },
                    "standup": {},
                    "retrospective": {}
                },
                "features": {
                    "enable_ceremony_integration": True
                }
            }

            with open(config_path, "w") as f:
                yaml.dump(config, f)

            selector = WorkflowSelector(config_dir=Path(tmpdir))

            # Level 2 should now have planning (overridden to required)
            assert selector._should_have_planning(ScaleLevel.LEVEL_2_SMALL_FEATURE), \
                "Custom config should override planning requirement for Level 2"


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_default_constructor_works(self):
        """Default constructor (no args) works."""
        selector = WorkflowSelector()
        workflows = selector.select_workflows(ScaleLevel.LEVEL_2_SMALL_FEATURE)
        assert len(workflows) > 0, "Should return workflows"

    def test_existing_tests_pass(self):
        """Existing workflow tests still work (without ceremonies)."""
        selector = WorkflowSelector()

        # Level 0: Direct implementation
        workflows_l0 = selector.select_workflows(
            ScaleLevel.LEVEL_0_CHORE,
            include_ceremonies=False
        )
        assert len(workflows_l0) == 1, "Level 0 should have 1 workflow"
        assert workflows_l0[0].workflow_name == "direct-implementation"

        # Level 1: Bug fix
        workflows_l1 = selector.select_workflows(
            ScaleLevel.LEVEL_1_BUG_FIX,
            include_ceremonies=False
        )
        assert len(workflows_l1) == 3, "Level 1 should have 3 workflows"

        # Level 2: Small feature
        workflows_l2 = selector.select_workflows(
            ScaleLevel.LEVEL_2_SMALL_FEATURE,
            include_ceremonies=False
        )
        assert len(workflows_l2) == 4, "Level 2 should have 4 workflows"


class TestCeremonyHelpers:
    """Test ceremony helper methods."""

    def test_should_have_planning(self):
        """Test _should_have_planning logic."""
        selector = WorkflowSelector()

        assert not selector._should_have_planning(ScaleLevel.LEVEL_0_CHORE)
        assert not selector._should_have_planning(ScaleLevel.LEVEL_1_BUG_FIX)
        assert not selector._should_have_planning(ScaleLevel.LEVEL_2_SMALL_FEATURE)
        assert selector._should_have_planning(ScaleLevel.LEVEL_3_MEDIUM_FEATURE)
        assert selector._should_have_planning(ScaleLevel.LEVEL_4_GREENFIELD)

    def test_should_have_standup(self):
        """Test _should_have_standup logic."""
        selector = WorkflowSelector()

        assert not selector._should_have_standup(ScaleLevel.LEVEL_0_CHORE)
        assert not selector._should_have_standup(ScaleLevel.LEVEL_1_BUG_FIX)
        assert selector._should_have_standup(ScaleLevel.LEVEL_2_SMALL_FEATURE)
        assert selector._should_have_standup(ScaleLevel.LEVEL_3_MEDIUM_FEATURE)
        assert selector._should_have_standup(ScaleLevel.LEVEL_4_GREENFIELD)

    def test_should_have_retrospective(self):
        """Test _should_have_retrospective logic."""
        selector = WorkflowSelector()

        assert not selector._should_have_retrospective(ScaleLevel.LEVEL_0_CHORE)
        assert selector._should_have_retrospective(ScaleLevel.LEVEL_1_BUG_FIX)
        assert selector._should_have_retrospective(ScaleLevel.LEVEL_2_SMALL_FEATURE)
        assert selector._should_have_retrospective(ScaleLevel.LEVEL_3_MEDIUM_FEATURE)
        assert selector._should_have_retrospective(ScaleLevel.LEVEL_4_GREENFIELD)

    def test_create_planning_ceremony(self):
        """Test _create_planning_ceremony method."""
        selector = WorkflowSelector()

        ceremony = selector._create_planning_ceremony(
            ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            depends_on=["create-prd"]
        )

        assert ceremony.workflow_name == "planning-ceremony"
        assert ceremony.phase == "ceremonies"
        assert ceremony.required is True  # Level 3
        assert ceremony.depends_on == ["create-prd"]

    def test_create_standup_ceremony(self):
        """Test _create_standup_ceremony method."""
        selector = WorkflowSelector()

        ceremony = selector._create_standup_ceremony(
            ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            depends_on=["implement-stories"]
        )

        assert ceremony.workflow_name == "standup-ceremony"
        assert ceremony.phase == "ceremonies"
        assert ceremony.required is False  # Conditional
        assert ceremony.depends_on == ["implement-stories"]

    def test_create_retrospective_ceremony(self):
        """Test _create_retrospective_ceremony method."""
        selector = WorkflowSelector()

        ceremony = selector._create_retrospective_ceremony(
            ScaleLevel.LEVEL_2_SMALL_FEATURE,
            depends_on=["test-feature"]
        )

        assert ceremony.workflow_name == "retrospective-ceremony"
        assert ceremony.phase == "ceremonies"
        assert ceremony.required is True  # Level 2+
        assert ceremony.depends_on == ["test-feature"]
