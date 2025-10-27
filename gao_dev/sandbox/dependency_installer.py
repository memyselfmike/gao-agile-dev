"""Dependency installation for boilerplate projects."""

import subprocess
import time
from pathlib import Path
from typing import Optional, List
from enum import Enum

import structlog

from .exceptions import SandboxError

logger = structlog.get_logger(__name__)


class PackageManager(Enum):
    """Supported package managers."""

    PIP = "pip"
    UV = "uv"
    NPM = "npm"
    YARN = "yarn"
    PNPM = "pnpm"
    BUNDLER = "bundler"
    CARGO = "cargo"
    GO = "go"


class DependencyInstallError(SandboxError):
    """Raised when dependency installation fails."""

    pass


class DependencyInstaller:
    """
    Handles dependency installation for various project types.

    Supports Python (pip/uv), Node.js (npm/yarn/pnpm), Ruby (bundler),
    Rust (cargo), and Go (go mod).
    """

    def __init__(self):
        """Initialize dependency installer."""
        self.max_retries = 3
        self.retry_delay = 2

    def install_dependencies(
        self,
        project_path: Path,
        timeout: int = 600,
    ) -> bool:
        """
        Auto-detect and install project dependencies.

        Args:
            project_path: Root directory of project
            timeout: Installation timeout in seconds

        Returns:
            True if successful, False otherwise

        Raises:
            DependencyInstallError: If installation fails
        """
        project_path = Path(project_path).resolve()

        if not project_path.exists():
            raise DependencyInstallError(f"Project path does not exist: {project_path}")

        logger.info("installing_dependencies", project_path=str(project_path))

        # Detect package managers needed
        package_managers = self.detect_package_managers(project_path)

        if not package_managers:
            logger.info("no_package_managers_detected")
            return True

        # Install for each package manager
        success = True
        for pm in package_managers:
            try:
                if pm in (PackageManager.NPM, PackageManager.YARN, PackageManager.PNPM):
                    success &= self.install_node_deps(project_path, pm)
                elif pm in (PackageManager.PIP, PackageManager.UV):
                    success &= self.install_python_deps(project_path, pm)
                elif pm == PackageManager.BUNDLER:
                    success &= self.install_ruby_deps(project_path)
                elif pm == PackageManager.CARGO:
                    success &= self.install_rust_deps(project_path)
                elif pm == PackageManager.GO:
                    success &= self.install_go_deps(project_path)
            except Exception as e:
                logger.error("install_failed", package_manager=pm.value, error=str(e))
                success = False

        return success

    def detect_package_managers(self, project_path: Path) -> List[PackageManager]:
        """
        Detect which package managers are needed.

        Args:
            project_path: Project directory

        Returns:
            List of detected package managers
        """
        detected = []

        # Node.js detection
        if (project_path / "package.json").exists():
            node_pm = self.detect_node_package_manager(project_path)
            detected.append(node_pm)

        # Python detection
        if (project_path / "requirements.txt").exists():
            detected.append(PackageManager.PIP)
        elif (project_path / "pyproject.toml").exists():
            # Prefer uv if available, else pip
            if self.is_package_manager_available(PackageManager.UV):
                detected.append(PackageManager.UV)
            else:
                detected.append(PackageManager.PIP)

        # Ruby detection
        if (project_path / "Gemfile").exists():
            detected.append(PackageManager.BUNDLER)

        # Rust detection
        if (project_path / "Cargo.toml").exists():
            detected.append(PackageManager.CARGO)

        # Go detection
        if (project_path / "go.mod").exists():
            detected.append(PackageManager.GO)

        logger.info("package_managers_detected", managers=[pm.value for pm in detected])
        return detected

    def detect_node_package_manager(self, project_path: Path) -> PackageManager:
        """
        Detect npm/yarn/pnpm from lockfile.

        Args:
            project_path: Project directory

        Returns:
            Detected package manager (defaults to npm)
        """
        if (project_path / "pnpm-lock.yaml").exists():
            return PackageManager.PNPM
        elif (project_path / "yarn.lock").exists():
            return PackageManager.YARN
        elif (project_path / "package-lock.json").exists():
            return PackageManager.NPM
        else:
            return PackageManager.NPM  # Default

    def install_node_deps(
        self, project_path: Path, package_manager: PackageManager = PackageManager.NPM
    ) -> bool:
        """
        Install Node.js dependencies.

        Args:
            project_path: Project directory
            package_manager: npm, yarn, or pnpm

        Returns:
            True if successful
        """
        if not self.is_package_manager_available(package_manager):
            logger.warning(
                "package_manager_not_available",
                package_manager=package_manager.value,
            )
            return False

        logger.info("installing_node_deps", package_manager=package_manager.value)

        cmd = [package_manager.value, "install"]

        return self._run_install_command(cmd, project_path, timeout=600)

    def install_python_deps(
        self, project_path: Path, package_manager: PackageManager = PackageManager.PIP
    ) -> bool:
        """
        Install Python dependencies.

        Args:
            project_path: Project directory
            package_manager: pip or uv

        Returns:
            True if successful
        """
        if not self.is_package_manager_available(package_manager):
            logger.warning(
                "package_manager_not_available",
                package_manager=package_manager.value,
            )
            return False

        logger.info("installing_python_deps", package_manager=package_manager.value)

        if (project_path / "requirements.txt").exists():
            if package_manager == PackageManager.UV:
                cmd = ["uv", "pip", "install", "-r", "requirements.txt"]
            else:
                cmd = ["pip", "install", "-r", "requirements.txt"]
        elif (project_path / "pyproject.toml").exists():
            if package_manager == PackageManager.UV:
                cmd = ["uv", "pip", "install", "."]
            else:
                cmd = ["pip", "install", "."]
        else:
            return True

        return self._run_install_command(cmd, project_path, timeout=300)

    def install_ruby_deps(self, project_path: Path) -> bool:
        """Install Ruby dependencies with bundler."""
        if not self.is_package_manager_available(PackageManager.BUNDLER):
            logger.warning("bundler_not_available")
            return False

        logger.info("installing_ruby_deps")
        cmd = ["bundle", "install"]
        return self._run_install_command(cmd, project_path, timeout=300)

    def install_rust_deps(self, project_path: Path) -> bool:
        """Install Rust dependencies with cargo."""
        if not self.is_package_manager_available(PackageManager.CARGO):
            logger.warning("cargo_not_available")
            return False

        logger.info("installing_rust_deps")
        cmd = ["cargo", "build"]
        return self._run_install_command(cmd, project_path, timeout=600)

    def install_go_deps(self, project_path: Path) -> bool:
        """Install Go dependencies."""
        if not self.is_package_manager_available(PackageManager.GO):
            logger.warning("go_not_available")
            return False

        logger.info("installing_go_deps")
        cmd = ["go", "mod", "download"]
        return self._run_install_command(cmd, project_path, timeout=300)

    def is_package_manager_available(self, pm: PackageManager) -> bool:
        """
        Check if package manager is installed.

        Args:
            pm: Package manager to check

        Returns:
            True if available
        """
        try:
            result = subprocess.run(
                [pm.value, "--version"],
                capture_output=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _run_install_command(
        self, cmd: List[str], cwd: Path, timeout: int = 600
    ) -> bool:
        """
        Run installation command with retry logic.

        Args:
            cmd: Command to run
            cwd: Working directory
            timeout: Timeout in seconds

        Returns:
            True if successful
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "running_install_command",
                    command=" ".join(cmd),
                    attempt=attempt,
                )

                result = subprocess.run(
                    cmd,
                    cwd=str(cwd),
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False,
                )

                if result.returncode == 0:
                    logger.info("install_successful", command=cmd[0])
                    return True

                # Check if retryable error
                if self._is_retryable_error(result.stderr):
                    if attempt < self.max_retries:
                        delay = self.retry_delay * (2 ** (attempt - 1))
                        logger.warning(
                            "install_failed_retrying",
                            attempt=attempt,
                            delay=delay,
                        )
                        time.sleep(delay)
                        continue

                # Non-retryable error
                logger.error(
                    "install_failed",
                    command=" ".join(cmd),
                    error=result.stderr,
                )
                return False

            except subprocess.TimeoutExpired:
                logger.error("install_timeout", command=" ".join(cmd))
                return False
            except Exception as e:
                logger.error("install_error", command=" ".join(cmd), error=str(e))
                return False

        return False

    def _is_retryable_error(self, error_msg: str) -> bool:
        """Check if error is retryable (network issues)."""
        if not error_msg:
            return False

        error_msg = error_msg.lower()
        retryable = ["network", "timeout", "connection", "econnrefused", "etimedout"]
        return any(pattern in error_msg for pattern in retryable)
