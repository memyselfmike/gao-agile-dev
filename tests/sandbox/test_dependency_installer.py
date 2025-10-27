"""Tests for DependencyInstaller functionality."""

from pathlib import Path
from unittest.mock import Mock, patch
import pytest
from gao_dev.sandbox import DependencyInstaller, PackageManager

class TestDependencyInstaller:
    """Tests for DependencyInstaller class."""
    
    @pytest.fixture
    def installer(self):
        """Create DependencyInstaller instance."""
        return DependencyInstaller()
    
    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create temporary project."""
        project = tmp_path / "test_project"
        project.mkdir()
        return project
    
    def test_detect_node_package_json(self, installer, temp_project):
        """Test detection of package.json."""
        (temp_project / "package.json").write_text("{}")
        
        managers = installer.detect_package_managers(temp_project)
        
        assert PackageManager.NPM in managers or PackageManager.PNPM in managers or PackageManager.YARN in managers
    
    def test_detect_pnpm_from_lockfile(self, installer, temp_project):
        """Test pnpm detection from lockfile."""
        (temp_project / "package.json").write_text("{}")
        (temp_project / "pnpm-lock.yaml").write_text("")
        
        pm = installer.detect_node_package_manager(temp_project)
        
        assert pm == PackageManager.PNPM
    
    def test_detect_yarn_from_lockfile(self, installer, temp_project):
        """Test yarn detection from lockfile."""
        (temp_project / "package.json").write_text("{}")
        (temp_project / "yarn.lock").write_text("")
        
        pm = installer.detect_node_package_manager(temp_project)
        
        assert pm == PackageManager.YARN
    
    def test_detect_python_requirements(self, installer, temp_project):
        """Test detection of requirements.txt."""
        (temp_project / "requirements.txt").write_text("requests==2.28.0")
        
        managers = installer.detect_package_managers(temp_project)
        
        assert PackageManager.PIP in managers
    
    def test_is_package_manager_available(self, installer):
        """Test checking if package manager is available."""
        # Python should be available since we're running tests with it
        result = installer.is_package_manager_available(PackageManager.PIP)
        assert result is True
    
    @patch('gao_dev.sandbox.dependency_installer.subprocess.run')
    def test_install_node_deps_success(self, mock_run, installer, temp_project):
        """Test successful Node.js dependency installation."""
        mock_run.return_value = Mock(returncode=0, stderr="", stdout="")
        
        (temp_project / "package.json").write_text("{}")
        
        result = installer.install_node_deps(temp_project, PackageManager.NPM)
        
        assert result is True
    
    @patch('gao_dev.sandbox.dependency_installer.subprocess.run')
    def test_install_python_deps_success(self, mock_run, installer, temp_project):
        """Test successful Python dependency installation."""
        mock_run.return_value = Mock(returncode=0, stderr="", stdout="")
        
        (temp_project / "requirements.txt").write_text("requests")
        
        result = installer.install_python_deps(temp_project, PackageManager.PIP)
        
        assert result is True
    
    def test_is_retryable_error(self, installer):
        """Test retryable error detection."""
        assert installer._is_retryable_error("network error")
        assert installer._is_retryable_error("connection timeout")
        assert not installer._is_retryable_error("syntax error")
