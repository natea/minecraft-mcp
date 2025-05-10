"""
Tests for the place_entities tool in the GDMC MCP server.
"""
import sys
import os
from pathlib import Path
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

# Add the project root to the Python path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.gdmc_mcp.models import EntityData, Vec3iInput
from src.gdmc_mcp.server import place_entities

@pytest.mark.asyncio
async def test_place_single_entity(mock_context, mock_editor, mock_interface):
    """Test that place_entities successfully places a single entity."""
    # Arrange
    entities = [
        EntityData(
            id="minecraft:zombie",
            pos=Vec3iInput(coords=[10, 64, 10])
        )
    ]
    
    # Patch the interface module
    with patch("src.gdmc_mcp.server.gdpc_interface", mock_interface):
        # Act
        result = await place_entities(entities, mock_context)
    
    # Assert
    assert result["success"] is True
    assert result["placed"] == 1
    assert mock_context.info.called

@pytest.mark.asyncio
async def test_place_multiple_entities(mock_context, mock_editor, mock_interface):
    """Test that place_entities successfully places multiple entities."""
    # Arrange
    entities = [
        EntityData(
            id="minecraft:zombie",
            pos=Vec3iInput(coords=[10, 64, 10])
        ),
        EntityData(
            id="minecraft:skeleton",
            pos=Vec3iInput(coords=[15, 64, 15])
        ),
        EntityData(
            id="minecraft:creeper",
            pos=Vec3iInput(coords=[20, 64, 20])
        )
    ]
    
    # Patch the interface module
    with patch("src.gdmc_mcp.server.gdpc_interface", mock_interface):
        # Act
        result = await place_entities(entities, mock_context)
    
    # Assert
    assert result["success"] is True
    assert result["placed"] == 3
    assert mock_context.info.called

@pytest.mark.asyncio
async def test_place_entity_with_nbt(mock_context, mock_editor, mock_interface):
    """Test that place_entities successfully places an entity with NBT data."""
    # Arrange
    entities = [
        EntityData(
            id="minecraft:zombie",
            pos=Vec3iInput(coords=[10, 64, 10]),
            nbt="{CustomName:'{\"text\":\"Test Zombie\"}',Invulnerable:1b}"
        )
    ]
    
    # Create a spy for the interface.placeEntities method
    place_entities_spy = MagicMock(return_value={"placed": 1})
    mock_interface.placeEntities = place_entities_spy
    
    # Patch the interface module
    with patch("src.gdmc_mcp.server.gdpc_interface", mock_interface):
        # Act
        result = await place_entities(entities, mock_context)
    
    # Assert
    assert result["success"] is True
    assert result["placed"] == 1
    
    # Verify the NBT data was passed correctly
    place_entities_spy.assert_called_once()
    call_args = place_entities_spy.call_args[0][0]  # First positional argument
    assert len(call_args) == 1
    assert call_args[0]["id"] == "minecraft:zombie"
    assert call_args[0]["nbt"] == "{CustomName:'{\"text\":\"Test Zombie\"}',Invulnerable:1b}"

@pytest.mark.asyncio
async def test_place_entities_max_limit(mock_context, mock_editor, mock_interface):
    """Test that place_entities handles the maximum entity limit."""
    # Arrange - create 51 entities (over the 50 limit)
    entities = [
        EntityData(
            id="minecraft:zombie",
            pos=Vec3iInput(coords=[x, 64, x])
        )
        for x in range(51)
    ]
    
    # Patch the interface module
    with patch("src.gdmc_mcp.server.gdpc_interface", mock_interface):
        # Act & Assert - should fail validation before reaching the tool
        with pytest.raises(ValueError):
            await place_entities(entities, mock_context)

@pytest.mark.asyncio
async def test_place_entities_error_handling(mock_context, mock_interface):
    """Test that place_entities handles errors properly."""
    # Arrange
    entities = [
        EntityData(
            id="minecraft:zombie",
            pos=Vec3iInput(coords=[10, 64, 10])
        )
    ]
    
    # Mock the interface to raise an exception
    mock_interface.placeEntities.side_effect = Exception("Test error")
    
    # Patch the interface module
    with patch("src.gdmc_mcp.server.gdpc_interface", mock_interface):
        # Act & Assert
        with pytest.raises(ValueError, match="Failed to place entities"):
            await place_entities(entities, mock_context)
    
    assert mock_context.error.called

@pytest.mark.asyncio
async def test_place_entities_missing_editor(mock_context, mock_interface):
    """Test that place_entities handles missing editor properly."""
    # Arrange
    entities = [
        EntityData(
            id="minecraft:zombie",
            pos=Vec3iInput(coords=[10, 64, 10])
        )
    ]
    
    # Remove editor from context
    mock_context.request_context.lifespan_context = {}
    
    # Patch the interface module
    with patch("src.gdmc_mcp.server.gdpc_interface", mock_interface):
        # Act & Assert
        with pytest.raises(RuntimeError, match="GDPC Editor not found"):
            await place_entities(entities, mock_context)