"""Tests for TemplateSubstitutor functionality."""

from pathlib import Path
import pytest
from gao_dev.sandbox import TemplateSubstitutor, SubstitutionError

class TestTemplateSubstitutor:
    """Tests for TemplateSubstitutor class."""
    
    @pytest.fixture
    def substitutor(self):
        """Create TemplateSubstitutor instance."""
        return TemplateSubstitutor()
    
    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create temporary project."""
        project = tmp_path / "test_project"
        project.mkdir()
        return project
    
    def test_substitute_double_brace(self, substitutor, temp_project):
        """Test {{VAR}} substitution."""
        file = temp_project / "README.md"
        file.write_text("# {{PROJECT_NAME}}")
        
        subs = substitutor.substitute_in_file(file, {"PROJECT_NAME": "MyApp"})
        
        assert subs == 1
        assert file.read_text() == "# MyApp"
    
    def test_substitute_double_underscore(self, substitutor, temp_project):
        """Test __VAR__ substitution."""
        file = temp_project / "config.py"
        file.write_text("NAME = '__PROJECT_NAME__'")
        
        subs = substitutor.substitute_in_file(file, {"PROJECT_NAME": "MyApp"})
        
        assert subs == 1
        assert "MyApp" in file.read_text()
    
    def test_multiple_variables_same_file(self, substitutor, temp_project):
        """Test multiple variables in one file."""
        file = temp_project / "test.md"
        file.write_text("# {{TITLE}}\nAuthor: {{AUTHOR}}")
        
        subs = substitutor.substitute_in_file(file, {
            "TITLE": "My Project",
            "AUTHOR": "John Doe"
        })
        
        assert subs == 2
        content = file.read_text()
        assert "My Project" in content
        assert "John Doe" in content
    
    def test_validate_value_valid(self, substitutor):
        """Test valid value validation."""
        assert substitutor.validate_value("my-app")
        assert substitutor.validate_value("MyApp123")
        assert substitutor.validate_value("my_app")
        assert substitutor.validate_value("My App")
        assert substitutor.validate_value("app.name")
    
    def test_validate_value_invalid(self, substitutor):
        """Test invalid value validation."""
        assert not substitutor.validate_value("")
        assert not substitutor.validate_value("-invalid")
        assert not substitutor.validate_value("invalid-")
        assert not substitutor.validate_value(None)
    
    def test_substitute_variables_full_project(self, substitutor, temp_project):
        """Test substituting across entire project."""
        (temp_project / "README.md").write_text("# {{PROJECT_NAME}}")
        (temp_project / "package.json").write_text('{"name": "{{project_name}}"}')
        
        result = substitutor.substitute_variables(
            temp_project,
            {"PROJECT_NAME": "TestApp", "project_name": "testapp"}
        )
        
        assert result.success
        assert result.files_modified == 2
        assert result.variables_substituted == 2
    
    def test_unsubstituted_variables_reported(self, substitutor, temp_project):
        """Test unsubstituted variables are reported."""
        (temp_project / "test.md").write_text("{{VAR1}} {{VAR2}}")
        
        result = substitutor.substitute_variables(
            temp_project,
            {"VAR1": "Value1"}
        )
        
        assert "VAR2" in result.unsubstituted_variables
    
    def test_rollback_substitution(self, substitutor, temp_project):
        """Test rollback functionality."""
        file = temp_project / "test.md"
        file.write_text("{{VAR}}")
        
        # Substitute with backup
        substitutor.substitute_variables(
            temp_project,
            {"VAR": "NewValue"},
            create_backup=True
        )
        
        # Rollback
        success = substitutor.rollback_substitution(temp_project)
        
        assert success
        assert file.read_text() == "{{VAR}}"
