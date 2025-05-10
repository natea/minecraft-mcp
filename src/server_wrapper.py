#!/usr/bin/env python3
"""
Wrapper script to run the GDMC MCP server module properly.
This avoids relative import issues.
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import and run the server
from src.gdmc_mcp.server import mcp

if __name__ == "__main__":
    mcp.run()