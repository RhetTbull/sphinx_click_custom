#!/usr/bin/env python3
"""Test runner script for sphinx_click_custom."""

import subprocess
import sys


def run_tests():
    """Run the test suite."""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_simple.py",
        "tests/test_formatting.py",
        "tests/test_edge_cases.py",
        "tests/test_directive_simple.py",
        "tests/test_integration_simple.py",
        "-v",
        "--tb=short",
    ]

    print("Running sphinx_click_custom test suite...")
    result = subprocess.run(cmd)
    return result.returncode


def run_tests_with_coverage():
    """Run tests with coverage report."""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_simple.py",
        "tests/test_formatting.py",
        "tests/test_edge_cases.py",
        "tests/test_directive_simple.py",
        "tests/test_integration_simple.py",
        "--cov=sphinx_click_custom",
        "--cov-report=term-missing",
        "--cov-report=html",
        "-v",
    ]

    print("Running sphinx_click_custom test suite with coverage...")
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    if "--coverage" in sys.argv:
        exit_code = run_tests_with_coverage()
    else:
        exit_code = run_tests()

    sys.exit(exit_code)
