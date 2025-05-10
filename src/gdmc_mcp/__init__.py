# src/gdmc_mcp/__init__.py
"""
GDMC MCP Bridge for Minecraft procedural generation.
"""

from fastmcp import FastMCP

# Export models for external use
from .models import BlockData, Vec3iInput, EntityData, StructureData

# Don't import server module here to avoid circular imports
# The mcp instance should be imported directly from server module