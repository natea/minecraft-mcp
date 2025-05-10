#!/bin/bash
# Simple script to run the tests for the GDMC MCP server

# Ensure we're in the project root directory
cd "$(dirname "$0")"

# Check if pytest and pytest-asyncio are installed
if ! python -c "import pytest, pytest_asyncio" 2>/dev/null; then
    echo "Installing test dependencies..."
    pip install pytest pytest-asyncio pytest-cov
fi

# Run the tests using our test runner
echo "Running tests..."
python tests/run_tests.py "$@"