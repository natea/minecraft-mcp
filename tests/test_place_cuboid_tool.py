"""
Tests for the place_cuboid tool in the GDMC MCP server.
"""
import sys
import os
from pathlib import Path
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

# Add the project root to the Python path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.gdmc_mcp.models import BlockData, Vec3iInput
from src.gdmc_mcp.server import place_cuboid

@pytest.mark.asyncio
async def test_place_solid_cuboid(mock_context, mock_editor, mock_geometry):
    """Test that place_cuboid successfully places a solid cuboid."""
    # Arrange
    corner1 = Vec3iInput(coords=[10, 64, 10])
    corner2 = Vec3iInput(coords=[15, 69, 15])
    block = BlockData(id="minecraft:stone")
    hollow = False
    
    # Patch the geometry module
    with patch("src.gdmc_mcp.server.geometry", mock_geometry):
        # Act
        result = await place_cuboid(corner1, corner2, block, hollow, mock_context)
    
    # Assert
    assert result["success"] is True
    assert result["corner1"] == [10, 64, 10]
    assert result["corner2"] == [15, 69, 15]
    assert "Block(minecraft:stone)" in result["block"]
    assert result["hollow"] is False
    assert mock_context.info.called

@pytest.mark.asyncio
async def test_place_hollow_cuboid(mock_context, mock_editor, mock_geometry):
    """Test that place_cuboid successfully places a hollow cuboid."""
    # Arrange
    corner1 = Vec3iInput(coords=[10, 64, 10])
    corner2 = Vec3iInput(coords=[15, 69, 15])
    block = BlockData(id="minecraft:stone")
    hollow = True
    
    # Patch the geometry module
    with patch("src.gdmc_mcp.server.geometry", mock_geometry):
        # Act
        result = await place_cuboid(corner1, corner2, block, hollow, mock_context)
    
    # Assert
    assert result["success"] is True
    assert result["corner1"] == [10, 64, 10]
    assert result["corner2"] == [15, 69, 15]
    assert "Block(minecraft:stone)" in result["block"]
    assert result["hollow"] is True
    assert mock_context.info.called

@pytest.mark.asyncio
async def test_place_cuboid_with_block_states(mock_context, mock_editor, mock_geometry):
    """Test that place_cuboid successfully places a cuboid with block states."""
    # Arrange
    corner1 = Vec3iInput(coords=[10, 64, 10])
    corner2 = Vec3iInput(coords=[15, 69, 15])
    block = BlockData(id="minecraft:oak_log", states={"axis": "y"})
    hollow = False
    
    # Patch the geometry module
    with patch("src.gdmc_mcp.server.geometry", mock_geometry):
        # Act
        result = await place_cuboid(corner1, corner2, block, hollow, mock_context)
    
    # Assert
    assert result["success"] is True
    assert result["corner1"] == [10, 64, 10]
    assert result["corner2"] == [15, 69, 15]
    assert "Block(minecraft:oak_log)" in result["block"]
    assert mock_context.info.called

@pytest.mark.asyncio
async def test_place_cuboid_error_handling(mock_context, mock_geometry):
    """Test that place_cuboid handles errors properly."""
    # Arrange
    corner1 = Vec3iInput(coords=[10, 64, 10])
    corner2 = Vec3iInput(coords=[15, 69, 15])
    block = BlockData(id="minecraft:stone")
    hollow = False
    
    # Create a mock geometry that raises an exception
    mock_geometry.placeCuboid.side_effect = Exception("Test error")
    
    # Patch the geometry module
    with patch("src.gdmc_mcp.server.geometry", mock_geometry):
        # Act & Assert
        with pytest.raises(ValueError, match="Failed to place cuboid"):
            await place_cuboid(corner1, corner2, block, hollow, mock_context)
    
    assert mock_context.error.called

@pytest.mark.asyncio
async def test_place_cuboid_missing_editor(mock_context, mock_geometry):
    """Test that place_cuboid handles missing editor properly."""
    # Arrange
    corner1 = Vec3iInput(coords=[10, 64, 10])
    corner2 = Vec3iInput(coords=[15, 69, 15])
    block = BlockData(id="minecraft:stone")
    hollow = False
    
    # Remove editor from context
    mock_context.request_context.lifespan_context = {}
    
    # Patch the geometry module
    with patch("src.gdmc_mcp.server.geometry", mock_geometry):
        # Act & Assert
        with pytest.raises(RuntimeError, match="GDPC Editor not found"):
            await place_cuboid(corner1, corner2, block, hollow, mock_context)

@pytest.mark.asyncio
async def test_place_cuboid_inverted_corners(mock_context, mock_editor, mock_geometry):
    """Test that place_cuboid works with inverted corners."""
    # Arrange - corner2 has smaller coordinates than corner1
    corner1 = Vec3iInput(coords=[15, 69, 15])
    corner2 = Vec3iInput(coords=[10, 64, 10])
    block = BlockData(id="minecraft:stone")
    hollow = False
    
    # Patch the geometry module
    with patch("src.gdmc_mcp.server.geometry", mock_geometry):
        # Act
        result = await place_cuboid(corner1, corner2, block, hollow, mock_context)
    
    # Assert
    assert result["success"] is True
    # The result should contain the corners as provided, not reordered
    assert result["corner1"] == [15, 69, 15]
    assert result["corner2"] == [10, 64, 10]
    assert "Block(minecraft:stone)" in result["block"]
    assert mock_context.info.called