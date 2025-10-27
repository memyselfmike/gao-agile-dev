"""Tests for BoilerplateValidator functionality."""

from pathlib import Path
import pytest
from gao_dev.sandbox import BoilerplateValidator, ValidationLevel

class TestBoilerplateValidator:
    """Tests for BoilerplateValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create BoilerplateValidator instance."""
        return BoilerplateValidator()
    
    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create temporary project."""
        project = tmp_path / "test_project"
        project.mkdir()
        return project
    
    def test_validate_structure_missing_readme(self, validator, temp_project):
        """Test detection of missing README."""
        issues = validator.validate_structure(temp_project)
        
        readme_issues = [i for i in issues if "README" in i.message]
        assert len(readme_issues) > 0
    
    def test_validate_structure_with_readme(self, validator, temp_project):
        """Test structure validation with README present."""
        (temp_project / "README.md").write_text("# Project")
        (temp_project / "package.json").write_text("{}")
        
        issues = validator.validate_structure(temp_project)
        
        # Should not have README warning
        readme_issues = [i for i in issues if "README" in i.message]
        assert len(readme_issues) == 0
    
    def test_validate_dependencies_node(self, validator, temp_project):
        """Test Node.js dependency validation."""
        (temp_project / "package.json").write_text("{}")
        
        issues = validator.validate_dependencies(temp_project)
        
        # Should warn about missing node_modules
        node_issues = [i for i in issues if "node_modules" in i.message]
        assert len(node_issues) > 0
    
    def test_validate_configuration_valid_json(self, validator, temp_project):
        """Test JSON validation."""
        (temp_project / "config.json").write_text('{"key": "value"}')
        
        issues = validator.validate_configuration(temp_project)
        
        json_errors = [i for i in issues if "JSON" in i.message and i.level == ValidationLevel.ERROR]
        assert len(json_errors) == 0
    
    def test_validate_configuration_invalid_json(self, validator, temp_project):
        """Test invalid JSON detection."""
        (temp_project / "config.json").write_text('{invalid json}')
        
        issues = validator.validate_configuration(temp_project)
        
        json_errors = [i for i in issues if "JSON" in i.message]
        assert len(json_errors) > 0
    
    def test_check_template_residue(self, validator, temp_project):
        """Test detection of unsubstituted variables."""
        (temp_project / "README.md").write_text("# {{PROJECT_NAME}}")
        
        unsubstituted = validator.check_for_template_residue(temp_project)
        
        assert "PROJECT_NAME" in unsubstituted
    
    def test_validate_project_complete(self, validator, temp_project):
        """Test complete project validation."""
        (temp_project / "README.md").write_text("# Project")
        (temp_project / "package.json").write_text("{}")
        (temp_project / ".gitignore").write_text("node_modules")
        (temp_project / "src").mkdir()
        
        report = validator.validate_project(temp_project)
        
        assert report is not None
        assert isinstance(report.passed, bool)
    
    def test_format_report(self, validator, temp_project):
        """Test report formatting."""
        (temp_project / "package.json").write_text("{}")
        
        report = validator.validate_project(temp_project)
        formatted = validator.format_report(report)
        
        assert "Validation Report" in formatted
        assert "Summary" in formatted
