"""
Tests for the resource endpoints in the GDMC MCP server.
"""
import sys
import os
from pathlib import Path
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import numpy as np

# Add the project root to the Python path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.gdmc_mcp.server import (
    get_build_area,
    get_players,
    get_entities,
    get_minecraft_version,
    get_heightmap_types,
    get_block,
    get_biome,
    get_height
)

@pytest.mark.asyncio
async def test_get_build_area(mock_context, mock_editor):
    """Test that get_build_area returns the correct build area."""
    # Arrange
    mock_editor._build_area.offset = (100, 60, 100)
    mock_editor._build_area.size = (50, 20, 50)
    mock_editor._build_area.end = (150, 80, 150)
    
    # Act
    result = await get_build_area(mock_context)
    
    # Assert
    assert result["offset"] == [100, 60, 100]
    assert result["size"] == [50, 20, 50]
    assert result["end"] == [150, 80, 150]
    assert mock_context.info.called

@pytest.mark.asyncio
async def test_get_build_area_not_set(mock_context, mock_editor):
    """Test that get_build_area handles build area not set."""
    # Arrange
    from gdpc.exceptions import BuildAreaNotSetError
    mock_editor.getBuildArea = MagicMock(side_effect=BuildAreaNotSetError("Build area not set"))
    
    # Act & Assert
    with pytest.raises(ValueError, match="Build area is not set"):
        await get_build_area(mock_context)
    
    assert mock_context.warning.called

@pytest.mark.asyncio
async def test_get_players(mock_context, mock_editor, mock_interface):
    """Test that get_players returns player data."""
    # Arrange
    expected_players = [
        {"name": "Player1", "uuid": "uuid1", "position": [0, 64, 0]},
        {"name": "Player2", "uuid": "uuid2", "position": [100, 70, 100]}
    ]
    mock_interface.getPlayers = MagicMock(return_value=expected_players)
    
    # Patch the interface module
    with patch("src.gdmc_mcp.server.gdpc_interface", mock_interface):
        # Act
        result = await get_players(mock_context)
    
    # Assert
    assert result == expected_players
    assert mock_context.info.called

@pytest.mark.asyncio
async def test_get_entities(mock_context, mock_editor, mock_interface):
    """Test that get_entities returns entity data."""
    # Arrange
    expected_entities = [
        {"id": "minecraft:zombie", "position": [10, 64, 10]},
        {"id": "minecraft:skeleton", "position": [20, 64, 20]}
    ]
    mock_interface.getEntities = MagicMock(return_value=expected_entities)
    
    # Patch the interface module
    with patch("src.gdmc_mcp.server.gdpc_interface", mock_interface):
        # Act
        result = await get_entities(mock_context)
    
    # Assert
    assert result == expected_entities
    assert mock_context.info.called

@pytest.mark.asyncio
async def test_get_minecraft_version(mock_context, mock_editor, mock_interface):
    """Test that get_minecraft_version returns the correct version."""
    # Arrange
    expected_version = "1.20.1"
    mock_interface.getVersion = MagicMock(return_value=expected_version)
    
    # Patch the interface module
    with patch("src.gdmc_mcp.server.gdpc_interface", mock_interface):
        # Act
        result = await get_minecraft_version(mock_context)
    
    # Assert
    assert result == {"version": expected_version}
    assert mock_context.info.called

@pytest.mark.asyncio
async def test_get_heightmap_types(mock_context):
    """Test that get_heightmap_types returns the correct heightmap types."""
    # Act
    result = await get_heightmap_types(mock_context)
    
    # Assert
    assert "heightmap_types" in result
    assert "WORLD_SURFACE" in result["heightmap_types"]
    assert "MOTION_BLOCKING" in result["heightmap_types"]
    assert "MOTION_BLOCKING_NO_LEAVES" in result["heightmap_types"]
    assert "OCEAN_FLOOR" in result["heightmap_types"]
    assert mock_context.info.called

@pytest.mark.asyncio
async def test_get_block(mock_context, mock_editor):
    """Test that get_block returns the correct block data."""
    # Arrange
    x, y, z = 10, 64, 10
    mock_block = mock_editor.getBlockGlobal(None)  # This will return a MockBlock from our fixture
    mock_block.id = "minecraft:stone"
    mock_block.states = {"variant": "granite"}
    mock_editor.getBlockGlobal = MagicMock(return_value=mock_block)
    
    # Act
    result = await get_block(x, y, z, mock_context)
    
    # Assert
    assert result["id"] == "minecraft:stone"
    assert result["states"] == {"variant": "granite"}
    assert mock_context.info.called

@pytest.mark.asyncio
async def test_get_block_void_air(mock_context, mock_editor):
    """Test that get_block handles void_air (out of world) correctly."""
    # Arrange
    x, y, z = 10000, 64, 10000  # Far outside the world
    mock_block = mock_editor.getBlockGlobal(None)
    mock_block.id = "minecraft:void_air"
    mock_editor.getBlockGlobal = MagicMock(return_value=mock_block)
    
    # Act & Assert
    with pytest.raises(ValueError, match="outside the loaded world"):
        await get_block(x, y, z, mock_context)

@pytest.mark.asyncio
async def test_get_biome(mock_context, mock_editor):
    """Test that get_biome returns the correct biome data."""
    # Arrange
    x, y, z = 10, 64, 10
    expected_biome = "minecraft:plains"
    mock_editor.getBiomeGlobal = MagicMock(return_value=expected_biome)
    
    # Act
    result = await get_biome(x, y, z, mock_context)
    
    # Assert
    assert result["biome_id"] == expected_biome
    assert result["position"] == [10, 64, 10]
    assert mock_context.info.called

@pytest.mark.asyncio
async def test_get_biome_empty(mock_context, mock_editor):
    """Test that get_biome handles empty biome response correctly."""
    # Arrange
    x, y, z = 10000, 64, 10000  # Far outside the world
    mock_editor.getBiomeGlobal = MagicMock(return_value="")
    
    # Act & Assert
    with pytest.raises(ValueError, match="outside the loaded world"):
        await get_biome(x, y, z, mock_context)

@pytest.mark.asyncio
async def test_get_height(mock_context, mock_editor):
    """Test that get_height returns the correct height data."""
    # Arrange
    heightmap_type = "WORLD_SURFACE"
    x, z = 10, 10
    
    # Create a mock world slice with a specific height value
    mock_world_slice = MagicMock()
    mock_world_slice.heightmaps = {
        "WORLD_SURFACE": np.array([[65]])  # Height value of 65
    }
    mock_editor.loadWorldSlice = MagicMock(return_value=mock_world_slice)
    
    # Act
    result = await get_height(heightmap_type, x, z, mock_context)
    
    # Assert
    assert result["heightmap_type"] == heightmap_type
    assert result["position"] == [x, z]
    assert result["height"] == 64  # Should be 65-1 because heightmaps contain the Y-level above terrain
    assert result["raw_height"] == 65
    assert mock_context.info.called

@pytest.mark.asyncio
async def test_get_height_invalid_type(mock_context):
    """Test that get_height handles invalid heightmap type."""
    # Arrange
    heightmap_type = "INVALID_TYPE"
    x, z = 10, 10
    
    # Act & Assert
    with pytest.raises(ValueError, match="Invalid heightmap type"):
        await get_height(heightmap_type, x, z, mock_context)

@pytest.mark.asyncio
async def test_get_height_missing_type(mock_context, mock_editor):
    """Test that get_height handles missing heightmap type."""
    # Arrange
    heightmap_type = "WORLD_SURFACE"
    x, z = 10, 10
    
    # Create a mock world slice with missing heightmap type
    mock_world_slice = MagicMock()
    mock_world_slice.heightmaps = {}  # No heightmaps available
    mock_editor.loadWorldSlice = MagicMock(return_value=mock_world_slice)
    
    # Act & Assert
    with pytest.raises(ValueError, match="Heightmap type .* not available"):
        await get_height(heightmap_type, x, z, mock_context)