"""Tests for file management endpoints.

Epic 39.4: File Management
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from gao_dev.web.server import create_app
from gao_dev.web.config import WebConfig


@pytest.fixture
def client(tmp_path):
    """Create test client with temporary project root."""
    # Create test project structure
    (tmp_path / "docs").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "gao_dev").mkdir()

    # Create some test files
    (tmp_path / "docs" / "README.md").write_text("# Test Readme")
    (tmp_path / "src" / "main.py").write_text("print('hello')")

    # Create .gitignore
    (tmp_path / ".gitignore").write_text("*.pyc\n__pycache__/\n")

    # Initialize git repo
    import subprocess
    subprocess.run(["git", "init"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True
    )

    # Create test config pointing to tmp_path
    config = WebConfig(
        frontend_dist_path=str(tmp_path / "dist")  # Will use tmp_path as project_root
    )

    # Override project_root detection by patching
    app = create_app(config)
    app.state.project_root = tmp_path

    return TestClient(app)


def test_get_file_tree(client, tmp_path):
    """Test GET /api/files/tree endpoint."""
    response = client.get("/api/files/tree")
    assert response.status_code == 200

    data = response.json()
    assert "tree" in data
    tree = data["tree"]

    # Should have 4 top-level directories
    assert len(tree) == 4

    # Check directory names
    dir_names = {node["name"] for node in tree}
    assert dir_names == {"docs", "src", "tests", "gao_dev"}

    # Find docs directory
    docs_node = next(n for n in tree if n["name"] == "docs")
    assert docs_node["type"] == "directory"
    assert "children" in docs_node
    assert len(docs_node["children"]) == 1

    # Check README.md file
    readme = docs_node["children"][0]
    assert readme["name"] == "README.md"
    assert readme["type"] == "file"
    assert readme["icon"] == "markdown"


def test_get_file_content(client, tmp_path):
    """Test GET /api/files/content endpoint."""
    response = client.get("/api/files/content?path=docs/README.md")
    assert response.status_code == 200

    data = response.json()
    assert data["path"] == "docs/README.md"
    assert data["content"] == "# Test Readme"
    assert data["language"] == "markdown"


def test_get_file_content_not_found(client):
    """Test GET /api/files/content with non-existent file."""
    response = client.get("/api/files/content?path=nonexistent.txt")
    assert response.status_code == 404


def test_get_file_content_security(client):
    """Test GET /api/files/content rejects path traversal."""
    response = client.get("/api/files/content?path=../../etc/passwd")
    assert response.status_code == 403


def test_save_file_invalid_commit_message(client):
    """Test POST /api/files/save rejects invalid commit message."""
    response = client.post(
        "/api/files/save",
        json={
            "path": "docs/test.md",
            "content": "# Test",
            "commit_message": "invalid message format"
        }
    )
    assert response.status_code == 400
    assert "format" in response.json()["detail"].lower()


def test_save_file_empty_commit_message(client):
    """Test POST /api/files/save rejects empty commit message."""
    response = client.post(
        "/api/files/save",
        json={
            "path": "docs/test.md",
            "content": "# Test",
            "commit_message": ""
        }
    )
    assert response.status_code == 400
    assert "required" in response.json()["detail"].lower()
