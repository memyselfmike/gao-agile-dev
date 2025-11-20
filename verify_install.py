#!/usr/bin/env python
"""Verify GAO-Dev development installation is correct.

This script checks that:
1. gao_dev imports from the correct location (project directory)
2. No stale copies exist in site-packages
3. Changes to source files will take effect
4. Installation is in editable mode
"""

import sys
from pathlib import Path
import site

def check_import_location():
    """Check where gao_dev is being imported from."""
    print("=" * 60)
    print("1. Checking import location...")
    print("=" * 60)

    try:
        import gao_dev
        import_path = Path(gao_dev.__file__).parent
        project_root = Path(__file__).parent
        expected_path = project_root / "gao_dev"

        print(f"[OK] gao_dev imports from: {import_path}")
        print(f"     Expected location:    {expected_path}")

        if import_path.resolve() == expected_path.resolve():
            print("[PASS] Importing from correct location")
            return True
        else:
            print("[FAIL] Importing from wrong location!")
            print("       This means changes to source files won't take effect.")
            return False

    except ImportError as e:
        print(f"[FAIL] Cannot import gao_dev: {e}")
        return False

def check_site_packages():
    """Check for stale copies in site-packages."""
    print("\n" + "=" * 60)
    print("2. Checking for stale copies in site-packages...")
    print("=" * 60)

    issues_found = []

    # Get all site-packages directories
    site_packages = [Path(p) for p in site.getsitepackages()]
    user_site = Path(site.getusersitepackages())
    all_sites = site_packages + [user_site]

    for site_dir in all_sites:
        gao_dev_dir = site_dir / "gao_dev"
        if gao_dev_dir.exists() and gao_dev_dir.is_dir():
            # Check if it's a symlink or real directory
            if not gao_dev_dir.is_symlink():
                print(f"[!] Found stale copy: {gao_dev_dir}")
                issues_found.append(gao_dev_dir)
            else:
                print(f"    Symlink found (OK): {gao_dev_dir}")

    if not issues_found:
        print("[PASS] No stale copies found")
        return True
    else:
        print(f"\n[FAIL] Found {len(issues_found)} stale cop{'y' if len(issues_found) == 1 else 'ies'}")
        print("\nTo fix, run:")
        for path in issues_found:
            print(f"  rmdir /s /q \"{path}\"")
        return False

def check_pip_installation():
    """Check pip installation details."""
    print("\n" + "=" * 60)
    print("3. Checking pip installation...")
    print("=" * 60)

    import subprocess

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "gao-dev"],
            capture_output=True,
            text=True,
            check=True
        )

        output = result.stdout
        print(output)

        if "Editable project location:" in output:
            print("[PASS] Installed in editable mode")
            return True
        else:
            print("[FAIL] Not installed in editable mode")
            print("       Run: pip install -e .")
            return False

    except subprocess.CalledProcessError:
        print("[FAIL] gao-dev not installed")
        print("       Run: pip install -e .")
        return False

def check_pycache():
    """Check for __pycache__ directories that might cause issues."""
    print("\n" + "=" * 60)
    print("4. Checking for Python bytecode cache...")
    print("=" * 60)

    project_root = Path(__file__).parent / "gao_dev"
    pycache_dirs = list(project_root.rglob("__pycache__"))

    if pycache_dirs:
        print(f"  Found {len(pycache_dirs)} __pycache__ directories")
        print("  (This is normal - bytecode is cached for performance)")
        print("  If you have import issues, clear with:")
        print("  for /d /r . %G in (\"__pycache__\") do @if exist \"%G\" rmdir /s /q \"%G\"")
    else:
        print("  No __pycache__ directories found")

    return True

def main():
    """Run all verification checks."""
    print("""
==================================================================
            GAO-Dev Installation Verification
==================================================================
""")

    results = []

    # Run all checks
    results.append(("Import Location", check_import_location()))
    results.append(("Site-Packages", check_site_packages()))
    results.append(("Pip Installation", check_pip_installation()))
    results.append(("Bytecode Cache", check_pycache()))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for check_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{check_name:.<40} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("""
[SUCCESS] Your development environment is correctly configured!

  Changes to source files will take effect immediately.
  You can now run: gao-dev start
""")
        return 0
    else:
        print("""
[ISSUES FOUND] Your development environment needs attention.

  Quick fix: Run the reinstall script
    > reinstall_dev.bat

  Or follow the manual steps in DEV_TROUBLESHOOTING.md
""")
        return 1

if __name__ == "__main__":
    sys.exit(main())
