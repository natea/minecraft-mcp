#!/usr/bin/env python3
"""
Test runner script for GDMC MCP server tests.
This script configures the test environment and runs pytest with appropriate options.
"""
import sys
import os
from pathlib import Path
import subprocess
import argparse

# Add the project root to the Python path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Run the tests with appropriate configuration."""
    parser = argparse.ArgumentParser(description="Run GDMC MCP server tests")
    parser.add_argument("--cov", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--verbose", "-v", action="store_true", help="Run with verbose output")
    parser.add_argument("--test-file", help="Run a specific test file")
    parser.add_argument("--test-function", help="Run a specific test function")
    args = parser.parse_args()
    
    # Build the pytest command
    cmd = ["pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    
    # Add coverage if requested
    if args.cov:
        cmd.extend(["--cov=src.gdmc_mcp", "--cov-report=term", "--cov-report=html"])
    
    # Add specific test file or function if provided
    if args.test_file:
        if args.test_function:
            cmd.append(f"tests/{args.test_file}::test_{args.test_function}")
        else:
            cmd.append(f"tests/{args.test_file}")
    elif args.test_function:
        cmd.append(f"tests/::test_{args.test_function}")
    else:
        cmd.append("tests/")
    
    # Print the command being run
    print(f"Running: {' '.join(cmd)}")
    
    # Run the tests
    result = subprocess.run(cmd)
    
    # Return the exit code from pytest
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())