#!/usr/bin/env python3
"""
Version Bump Calculator

Analyzes git commits since last tag to determine next semantic version.
Follows Conventional Commits specification:
- feat: MINOR bump
- fix: PATCH bump
- BREAKING CHANGE: MAJOR bump
- chore/docs/test: No bump (but valid for changelog)

Usage:
    python scripts/bump_version.py              # Auto-detect from git
    python scripts/bump_version.py 0.1.0 minor  # Manual bump
    python scripts/bump_version.py 0.1.0 patch
    python scripts/bump_version.py 0.1.0 major
"""

import re
import subprocess
import sys
from typing import Tuple, List, Optional


def run_command(cmd: List[str]) -> str:
    """Run shell command and return output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Command failed: {' '.join(cmd)}", file=sys.stderr)
        print(f"  Output: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def get_latest_tag() -> Optional[str]:
    """Get the latest git tag, or None if no tags exist."""
    try:
        tag = run_command(["git", "describe", "--tags", "--abbrev=0"])
        return tag
    except:
        return None


def parse_version(version: str) -> Tuple[int, int, int, str]:
    """
    Parse semantic version string.

    Args:
        version: Version string (e.g., "1.2.3-beta.1")

    Returns:
        Tuple of (major, minor, patch, prerelease)
    """
    # Remove 'v' prefix if present
    version = version.lstrip('v')

    # Split prerelease suffix
    if '-' in version:
        base, prerelease = version.split('-', 1)
    else:
        base, prerelease = version, ''

    # Parse major.minor.patch
    parts = base.split('.')
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {version}")

    major, minor, patch = map(int, parts)

    return major, minor, patch, prerelease


def get_commits_since_tag(tag: Optional[str]) -> List[str]:
    """Get list of commit messages since given tag (or all commits if no tag)."""
    if tag:
        cmd = ["git", "log", f"{tag}..HEAD", "--pretty=format:%s"]
    else:
        cmd = ["git", "log", "--pretty=format:%s"]

    output = run_command(cmd)
    if not output:
        return []

    return output.split('\n')


def analyze_commits(commits: List[str]) -> Tuple[str, List[str]]:
    """
    Analyze commits to determine bump type.

    Returns:
        (bump_type, matching_commits) where bump_type is "major", "minor", "patch", or "none"
    """
    has_breaking = False
    has_feat = False
    has_fix = False

    breaking_pattern = re.compile(r'BREAKING CHANGE', re.IGNORECASE)
    feat_pattern = re.compile(r'^feat(\(.+?\))?:', re.IGNORECASE)
    fix_pattern = re.compile(r'^fix(\(.+?\))?:', re.IGNORECASE)

    breaking_commits = []
    feat_commits = []
    fix_commits = []

    for commit in commits:
        if breaking_pattern.search(commit):
            has_breaking = True
            breaking_commits.append(commit)
        elif feat_pattern.match(commit):
            has_feat = True
            feat_commits.append(commit)
        elif fix_pattern.match(commit):
            has_fix = True
            fix_commits.append(commit)

    if has_breaking:
        return ("major", breaking_commits)
    elif has_feat:
        return ("minor", feat_commits)
    elif has_fix:
        return ("patch", fix_commits)
    else:
        # No version-bumping commits
        return ("none", [])


def bump_version(version: str, bump_type: str) -> str:
    """
    Bump version according to type.

    Args:
        version: Current version string
        bump_type: One of 'major', 'minor', 'patch'

    Returns:
        New version string

    Examples:
        >>> bump_version("0.1.0", "minor")
        '0.2.0'
        >>> bump_version("0.1.5", "patch")
        '0.1.6'
        >>> bump_version("0.9.9", "major")
        '1.0.0'
    """
    major, minor, patch, _ = parse_version(version)

    if bump_type == 'major':
        return f"{major + 1}.0.0"
    elif bump_type == 'minor':
        return f"{major}.{minor + 1}.0"
    elif bump_type == 'patch':
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}. Use major, minor, or patch.")


def calculate_next_version(
    current: Optional[str],
    bump_type: str
) -> str:
    """
    Calculate next version based on current version and bump type.

    Args:
        current: Current version string (e.g., "v0.1.0" or None)
        bump_type: "major", "minor", "patch", or "none"

    Returns:
        Next version string (e.g., "0.2.0")
    """
    if current is None:
        # No existing tags - start at 0.1.0
        return "0.1.0"

    if bump_type == "none":
        # No bump needed - return current version
        major, minor, patch, _ = parse_version(current)
        return f"{major}.{minor}.{patch}"

    return bump_version(current, bump_type)


def main() -> int:
    """Main entry point."""
    # Check if manual mode (version and bump type provided)
    if len(sys.argv) == 3:
        # Manual mode: bump_version.py <version> <major|minor|patch>
        try:
            current_version = sys.argv[1]
            bump_type = sys.argv[2]

            next_version = bump_version(current_version, bump_type)
            print(next_version)
            return 0

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    elif len(sys.argv) != 1:
        print("Usage: bump_version.py [<version> <major|minor|patch>]", file=sys.stderr)
        print("", file=sys.stderr)
        print("Auto mode (no arguments):", file=sys.stderr)
        print("  Analyzes git commits to determine bump type", file=sys.stderr)
        print("", file=sys.stderr)
        print("Manual mode:", file=sys.stderr)
        print("  bump_version.py 0.1.0 minor  # → 0.2.0", file=sys.stderr)
        print("  bump_version.py 0.1.0 patch  # → 0.1.1", file=sys.stderr)
        print("  bump_version.py 0.1.0 major  # → 1.0.0", file=sys.stderr)
        return 1

    # Auto mode: analyze git commits
    print("=== Version Bump Calculator ===\n", file=sys.stderr)

    # Check if we're in a git repository
    try:
        run_command(["git", "rev-parse", "--git-dir"])
    except:
        print("ERROR: Not a git repository", file=sys.stderr)
        return 1

    # Get latest tag
    latest_tag = get_latest_tag()
    if latest_tag:
        print(f"Latest tag: {latest_tag}", file=sys.stderr)
    else:
        print("No existing tags found", file=sys.stderr)

    # Get commits since tag
    commits = get_commits_since_tag(latest_tag)
    print(f"Commits since tag: {len(commits)}", file=sys.stderr)

    if not commits:
        print("\nNo new commits since last tag", file=sys.stderr)
        if latest_tag:
            current_version = latest_tag.lstrip('v').split('-')[0]
            print(f"Current version: {current_version}", file=sys.stderr)
            print(current_version)  # Output to stdout for CI/CD
        else:
            print("0.1.0")  # Default starting version
        return 0

    # Analyze commits
    bump_type, matching_commits = analyze_commits(commits)

    print(f"\nBump type: {bump_type.upper()}", file=sys.stderr)
    if matching_commits:
        print(f"Matching commits: {len(matching_commits)}", file=sys.stderr)
        for commit in matching_commits[:5]:  # Show first 5
            print(f"  - {commit[:80]}", file=sys.stderr)
        if len(matching_commits) > 5:
            print(f"  ... and {len(matching_commits) - 5} more", file=sys.stderr)

    # Calculate next version
    next_version = calculate_next_version(latest_tag, bump_type)

    print(f"\nNext version: {next_version}", file=sys.stderr)
    print(next_version)  # Output to stdout for CI/CD
    return 0


if __name__ == '__main__':
    sys.exit(main())
