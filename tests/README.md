# GDMC MCP Server Tests

This directory contains unit tests for the GDMC MCP server tools and resources.

## Test Structure

- `conftest.py` - Contains pytest fixtures and mock implementations of GDPC classes
- `test_place_block_tool.py` - Tests for the place_block tool
- `test_run_command_tool.py` - Tests for the run_command tool
- `test_place_cuboid_tool.py` - Tests for the place_cuboid tool
- `test_place_entities_tool.py` - Tests for the place_entities tool
- `test_place_structure_tool.py` - Tests for the place_structure tool
- `test_resources.py` - Tests for all resource endpoints
- `test_server_lifespan.py` - Tests for server lifespan and utility functions

## Running Tests

### Prerequisites

Make sure you have pytest and pytest-asyncio installed:

```bash
pip install pytest pytest-asyncio
```

### Running All Tests

From the project root directory:

```bash
pytest tests/
```

### Running Specific Test Files

```bash
pytest tests/test_place_block_tool.py
```

### Running with Coverage

To run tests with coverage reporting:

```bash
pip install pytest-cov
pytest --cov=src.gdmc_mcp tests/
```

## Test Design

These tests use mocking to simulate the GDPC Editor and Minecraft interface without requiring an actual Minecraft server. This allows for fast, reliable testing of the MCP server's functionality.

Key mocking strategies:
- Mock GDPC Editor class to simulate block placement and world queries
- Mock interface module for entity and structure placement
- Mock geometry module for cuboid placement
- Mock Context class for FastMCP integration

## Adding New Tests

When adding new tools or resources to the server, follow these guidelines for testing:

1. Create test cases for successful operations
2. Test with various input parameters
3. Test error handling and edge cases
4. Mock any external dependencies
5. Use descriptive test names that explain what's being tested