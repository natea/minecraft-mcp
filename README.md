# FastMCP GDMC Bridge

A bridge between [FastMCP](https://github.com/fastmcp/fastmcp) and [GDPC](https://github.com/avdstaaij/gdpc) for Minecraft generative design.

## Overview

This project provides a [FastMCP](https://github.com/fastmcp/fastmcp) server that exposes GDPC (Generative Design Python Client) functionality through a standardized API. This allows AI assistants and other applications to interact with Minecraft worlds using the GDMC HTTP interface.

## Features

- **Block Placement**: Place individual blocks or geometric shapes
- **Terrain Analysis**: Analyze terrain features and heightmaps
- **Structure Building**: Build various structures with transformations
- **Model Creation**: Create and place complex models
- **Entity Placement**: Spawn entities in the world
- **Command Execution**: Run Minecraft commands
- **World Information**: Access block, biome, and player data

## Prerequisites

- Minecraft Java Edition with [GDMC HTTP Interface mod](https://github.com/Niels-NTG/gdmc_http_interface) (v1.6.0+)
- Python 3.8+

## Installation

```bash
# Clone the repository
git clone https://github.com/natea/fastmcp-gdmc-bridge.git
cd fastmcp-gdmc-bridge

# Create and activate a virtualenv
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .
```

## Usage

### Starting the Server

```bash
# Start the server with stdio transport (for AI assistants)
python -m gdmc_mcp.server

# Or start with SSE transport (for web applications)
fastmcp run gdmc_mcp.server --transport sse
```

### Client Example

```python
import asyncio
from fastmcp import Client

async def main():
    # Connect to the server
    async with Client() as client:
        # Get the build area
        build_area = await client.access_resource("gdmc://build_area")
        print(f"Build area: {build_area}")
        
        # Place a block
        result = await client.use_tool(
            "place_block",
            {
                "position": {"coords": [0, 65, 0]},
                "block": {"id": "stone"}
            }
        )
        print(f"Block placed: {result}")
        
        # Build a house with transformation
        result = await client.use_tool(
            "build_with_transform",
            {
                "position": {"coords": [10, 65, 10]},
                "rotation": 1,
                "flip": [False, False, False],
                "build_function": "house",
                "size": 7,
                "block": "oak_planks"
            }
        )
        print(f"House built: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

See `src/client_example.py` for a more comprehensive example.

## API Reference

### Tools

- **place_block**: Places a block at specified coordinates
- **run_command**: Executes Minecraft commands
- **place_cuboid**: Places solid or hollow cuboids
- **analyze_terrain**: Analyzes terrain features
- **build_with_transform**: Builds structures with transformations
- **create_and_place_model**: Creates and places complex models
- **place_entities**: Places entities in the world

### Resources

- **gdmc://build_area**: Returns the current build area
- **gdmc://players**: Returns information about online players
- **gdmc://minecraft_version**: Returns the Minecraft server version
- **gdmc://block/{x}/{y}/{z}**: Returns block information at coordinates
- **gdmc://biome/{x}/{y}/{z}**: Returns biome information at coordinates

## Development

### Project Structure

```
fastmcp-gdmc-bridge/
├── src/
│   ├── gdmc_mcp/
│   │   ├── __init__.py
│   │   ├── server.py
│   │   ├── models.py
│   │   ├── gdpc_utils.py
│   │   ├── tutorial_tools.py
│   │   └── py.typed
│   ├── client.py
│   └── client_example.py
├── tests/
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_place_block_tool.py
│   ├── test_run_command_tool.py
│   ├── test_place_cuboid_tool.py
│   ├── test_place_entities_tool.py
│   ├── test_place_structure_tool.py
│   ├── test_resources.py
│   ├── test_server_lifespan.py
│   ├── run_tests.py
│   └── README.md
├── pyproject.toml
└── README.md
```

### Running Tests

The project includes a comprehensive test suite that uses mocking to test the functionality without requiring a running Minecraft server.

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
cd fastmcp-gdmc-bridge
./tests/run_tests.py

# Run with coverage report
./tests/run_tests.py --cov

# Run specific test file
./tests/run_tests.py --test-file test_place_block_tool.py

# Run with verbose output
./tests/run_tests.py --verbose
```

See `tests/README.md` for more details on the test suite.

### Adding New Tools

To add a new tool to the server, add a new function to `server.py` with the `@mcp.tool()` decorator:

```python
@mcp.tool()
async def my_new_tool(
    param1: Annotated[str, Field(description="Description of param1")],
    ctx: Context
) -> dict[str, Any]:
    """Tool description."""
    editor = _get_editor(ctx)
    # Implement tool functionality
    return {"result": "success"}
```

When adding new tools, be sure to also add corresponding tests in the `tests/` directory.

## License

MIT

## Acknowledgements

- [GDPC](https://github.com/avdstaaij/gdpc) - Generative Design Python Client
- [FastMCP](https://github.com/fastmcp/fastmcp) - Framework for building MCP servers
- [GDMC HTTP Interface](https://github.com/Niels-NTG/gdmc_http_interface) - Minecraft mod for HTTP interaction