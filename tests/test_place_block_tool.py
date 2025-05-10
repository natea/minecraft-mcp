"""
Tests for the place_block tool in the GDMC MCP server.
"""
import sys
import os
from pathlib import Path
import pytest
from unittest.mock import patch, AsyncMock

# Add the project root to the Python path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.gdmc_mcp.models import BlockData, Vec3iInput
from src.gdmc_mcp.server import place_block

@pytest.mark.asyncio
async def test_place_block_success(mock_context, mock_editor):
    """Test that place_block successfully places a block."""
    # Arrange
    position = Vec3iInput(coords=[10, 64, 10])
    block = BlockData(id="minecraft:stone")
    
    # Act
    result = await place_block(position, block, mock_context)
    
    # Assert
    assert result["success"] is True
    assert result["position"] == [10, 64, 10]
    assert result["block"] == "Block(minecraft:stone)"
    assert mock_context.info.called
    
    # Verify the block was placed in the mock editor
    assert tuple(position.to_ivec3()) in mock_editor._blocks
    assert mock_editor._blocks[tuple(position.to_ivec3())].id == "minecraft:stone"

@pytest.mark.asyncio
async def test_place_block_with_states(mock_context, mock_editor):
    """Test that place_block successfully places a block with states."""
    # Arrange
    position = Vec3iInput(coords=[10, 64, 10])
    block = BlockData(id="minecraft:oak_stairs", states={"facing": "north", "half": "bottom"})
    
    # Act
    result = await place_block(position, block, mock_context)
    
    # Assert
    assert result["success"] is True
    assert result["position"] == [10, 64, 10]
    assert "Block(minecraft:oak_stairs)" in result["block"]
    
    # Verify the block was placed with correct states
    placed_block = mock_editor._blocks[tuple(position.to_ivec3())]
    assert placed_block.id == "minecraft:oak_stairs"
    assert placed_block.states == {"facing": "north", "half": "bottom"}

@pytest.mark.asyncio
async def test_place_block_with_data(mock_context, mock_editor):
    """Test that place_block successfully places a block with data."""
    # Arrange
    position = Vec3iInput(coords=[10, 64, 10])
    block_data = '{"Items":[{"id":"minecraft:diamond","Count":64,"Slot":0}]}'
    block = BlockData(id="minecraft:chest", data=block_data)
    
    # Act
    result = await place_block(position, block, mock_context)
    
    # Assert
    assert result["success"] is True
    assert result["position"] == [10, 64, 10]
    assert "Block(minecraft:chest)" in result["block"]
    
    # Verify the block was placed with correct data
    placed_block = mock_editor._blocks[tuple(position.to_ivec3())]
    assert placed_block.id == "minecraft:chest"
    assert placed_block.data == block_data

@pytest.mark.asyncio
async def test_place_block_error_handling(mock_context, mock_editor):
    """Test that place_block handles errors properly."""
    # Arrange
    position = Vec3iInput(coords=[10, 64, 10])
    block = BlockData(id="minecraft:stone")
    
    # Create a custom mock editor that raises an exception
    def place_block_error(*args, **kwargs):
        raise Exception("Test error")
    
    # Replace the placeBlock method with our error-raising version
    mock_editor.placeBlock = place_block_error
    
    # Act & Assert
    with pytest.raises(ValueError, match="Failed to place block"):
        await place_block(position, block, mock_context)
    
    assert mock_context.error.called

@pytest.mark.asyncio
async def test_place_block_missing_editor(mock_context):
    """Test that place_block handles missing editor properly."""
    # Arrange
    position = Vec3iInput(coords=[10, 64, 10])
    block = BlockData(id="minecraft:stone")
    
    # Remove editor from context
    mock_context.request_context.lifespan_context = {}
    
    # Act & Assert
    with pytest.raises(RuntimeError, match="GDPC Editor not found"):
        await place_block(position, block, mock_context)