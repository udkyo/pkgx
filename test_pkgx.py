#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "pytest>=7.0.0",
# ]
# [tool.uv]
# exclude-newer = "2025-02-19T00:00:00Z"
# ///

"""
Comprehensive test suite for pkgx (Universal Package Manager)
This script can run on any platform and tests all pkgx functionality.
"""

import os
import sys
import subprocess
import platform
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the pkgx package to the path so we can import it
sys.path.insert(0, str(Path(__file__).parent / "pkgx"))

try:
    from pkgx.managers import detect_package_manager, PACKAGE_MANAGERS
    from pkgx.cli import main as cli_main
except ImportError as e:
    print(f"Error importing pkgx modules: {e}")
    print("Make sure you're running this from the pkgx directory")
    sys.exit(1)


class TestResult:
    """Container for test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_pass(self, test_name: str):
        self.passed += 1
        print(f"✅ PASS: {test_name}")

    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"❌ FAIL: {test_name} - {error}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n📊 Test Summary:")
        print(f"Total tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        if self.errors:
            print(f"\n🔍 Failures:")
            for error in self.errors:
                print(f"  • {error}")
        return self.failed == 0


def run_pkgx_command(args: List[str]) -> tuple[int, str, str]:
    """Run pkgx command and return exit code, stdout, stderr"""
    try:
        # Get the pkgx package path and fix Windows path escaping
        pkgx_path = str(Path(__file__).parent / "pkgx").replace("\\", "\\\\")

        # Run pkgx as a subprocess
        result = subprocess.run(
            [sys.executable, "-c", f"""
import sys
sys.path.insert(0, r"{pkgx_path}")
from pkgx.cli import main
sys.argv = ["pkgx"] + {args}
sys.exit(main())
"""],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)


def test_help_command(results: TestResult):
    """Test that help command works"""
    exit_code, stdout, stderr = run_pkgx_command(["--help"])

    if exit_code == 0 and "Universal Package Manager" in stdout:
        results.add_pass("Help command")
    else:
        results.add_fail("Help command", f"Exit code: {exit_code}, stderr: {stderr}")


def test_version_command(results: TestResult):
    """Test version command"""
    exit_code, stdout, stderr = run_pkgx_command(["version"])

    if exit_code == 0 and "pkgx version" in stdout:
        results.add_pass("Version command")
    else:
        results.add_fail("Version command", f"Exit code: {exit_code}, stderr: {stderr}")


def test_list_managers_command(results: TestResult):
    """Test list-managers command"""
    exit_code, stdout, stderr = run_pkgx_command(["list-managers"])

    if exit_code == 0 and "Available package managers:" in stdout:
        results.add_pass("List managers command")

        # Check that all expected managers are listed
        expected_managers = ["apt", "dnf", "yum", "microdnf", "zypper", "apk", "brew", "chocolatey"]
        missing_managers = []
        for manager in expected_managers:
            if manager not in stdout:
                missing_managers.append(manager)

        if missing_managers:
            results.add_fail("Manager listing completeness", f"Missing managers: {missing_managers}")
        else:
            results.add_pass("All managers listed")
    else:
        results.add_fail("List managers command", f"Exit code: {exit_code}, stderr: {stderr}")


def test_dry_run_commands(results: TestResult):
    """Test dry-run functionality for all commands"""
    test_cases = [
        (["install", "git", "--dry-run"], "Would run:"),
        (["remove", "git", "--dry-run"], "Would run:"),
        (["update", "--dry-run"], "Would run:"),
        (["upgrade", "--dry-run"], "Would run:"),
        (["search", "python", "--dry-run"], "Would run:"),
    ]

    for args, expected_output in test_cases:
        exit_code, stdout, stderr = run_pkgx_command(args)

        if exit_code == 0 and expected_output in stdout:
            results.add_pass(f"Dry run: {' '.join(args[:-1])}")
        else:
            results.add_fail(f"Dry run: {' '.join(args[:-1])}",
                           f"Exit code: {exit_code}, stdout: {stdout[:100]}")


def test_manager_detection(results: TestResult):
    """Test package manager detection"""
    try:
        detected_pm = detect_package_manager()

        if detected_pm is not None:
            results.add_pass("Package manager detection")

            # Verify the detected manager is actually available
            if detected_pm.is_available():
                results.add_pass("Detected manager availability")
            else:
                results.add_fail("Detected manager availability",
                               f"Manager {detected_pm.name} not actually available")
        else:
            # On some systems, no package manager might be available
            # This isn't necessarily a failure, especially in containers
            results.add_pass("Package manager detection (none found)")

    except Exception as e:
        results.add_fail("Package manager detection", str(e))


def test_manual_manager_selection(results: TestResult):
    """Test manual manager selection"""
    # Find an available manager to test with
    available_managers = [pm for pm in PACKAGE_MANAGERS if pm.is_available()]

    if not available_managers:
        results.add_pass("Manual manager selection (skipped - no managers available)")
        return

    test_manager = available_managers[0]

    # Test with dry-run to avoid actually installing anything
    exit_code, stdout, stderr = run_pkgx_command([
        "install", "git", "--manager", test_manager.name, "--dry-run"
    ])

    if exit_code == 0 and test_manager.command in stdout:
        results.add_pass("Manual manager selection")
    else:
        results.add_fail("Manual manager selection",
                       f"Exit code: {exit_code}, expected {test_manager.command} in output")


def test_invalid_manager_selection(results: TestResult):
    """Test invalid manager selection"""
    exit_code, stdout, stderr = run_pkgx_command([
        "install", "git", "--manager", "nonexistent", "--dry-run"
    ])

    if exit_code != 0:
        results.add_pass("Invalid manager rejection")
    else:
        results.add_fail("Invalid manager rejection", "Should have failed with invalid manager")


def test_no_packages_error(results: TestResult):
    """Test that commands requiring packages fail appropriately"""
    exit_code, stdout, stderr = run_pkgx_command(["install"])

    if exit_code != 0:
        results.add_pass("No packages error handling")
    else:
        results.add_fail("No packages error handling", "Should have failed without packages")


def test_platform_specific_detection(results: TestResult):
    """Test platform-specific package manager detection logic"""
    system = platform.system()

    # This test verifies that detection logic makes sense for the platform
    # but doesn't require specific managers to be installed

    detected_pm = detect_package_manager()

    if system == "Windows":
        if detected_pm and detected_pm.name == "chocolatey":
            results.add_pass("Windows platform detection")
        elif detected_pm is None:
            results.add_pass("Windows platform detection (no manager found)")
        else:
            results.add_fail("Windows platform detection",
                           f"Unexpected manager: {detected_pm.name if detected_pm else 'None'}")

    elif system == "Darwin":  # macOS
        if detected_pm and detected_pm.name == "brew":
            results.add_pass("macOS platform detection")
        elif detected_pm is None:
            results.add_pass("macOS platform detection (no manager found)")
        else:
            results.add_fail("macOS platform detection",
                           f"Unexpected manager: {detected_pm.name if detected_pm else 'None'}")

    elif system == "Linux":
        # Linux can have various package managers, so we're more flexible
        if detected_pm:
            linux_managers = ["apt", "dnf", "yum", "zypper", "apk", "microdnf"]
            if detected_pm.name in linux_managers:
                results.add_pass("Linux platform detection")
            else:
                results.add_fail("Linux platform detection",
                               f"Unexpected manager: {detected_pm.name}")
        else:
            results.add_pass("Linux platform detection (no manager found)")

    else:
        results.add_pass(f"Platform detection ({system} - unknown platform)")


def run_all_tests() -> bool:
    """Run all tests and return True if all passed"""
    results = TestResult()

    print("🧪 Running pkgx Test Suite")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    print("-" * 50)

    # Run all test functions
    test_functions = [
        test_help_command,
        test_version_command,
        test_list_managers_command,
        test_dry_run_commands,
        test_manager_detection,
        test_manual_manager_selection,
        test_invalid_manager_selection,
        test_no_packages_error,
        test_platform_specific_detection,
    ]

    for test_func in test_functions:
        try:
            test_func(results)
        except Exception as e:
            results.add_fail(test_func.__name__, f"Test crashed: {e}")

    print("-" * 50)
    success = results.summary()

    if success:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n💥 {results.failed} test(s) failed!")

    return success


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)