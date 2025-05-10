"""
Tests for the place_structure tool in the GDMC MCP server.
"""
import sys
import os
from pathlib import Path
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

# Add the project root to the Python path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.gdmc_mcp.models import StructureData, Vec3iInput
from src.gdmc_mcp.server import place_structure

@pytest.mark.asyncio
async def test_place_structure_basic(mock_context, mock_editor, mock_interface):
    """Test that place_structure successfully places a basic structure."""
    # Arrange
    structure = StructureData(
        name="village/plains/houses/small_house_1",
        position=Vec3iInput(coords=[10, 64, 10])
    )
    
    # Patch the interface module
    with patch("src.gdmc_mcp.server.gdpc_interface", mock_interface):
        # Act
        result = await place_structure(structure, mock_context)
    
    # Assert
    assert result["success"] is True
    assert result["structure"] == "village/plains/houses/small_house_1"
    assert result["position"] == [10, 64, 10]
    assert mock_context.info.called

@pytest.mark.asyncio
async def test_place_structure_with_rotation(mock_context, mock_editor, mock_interface):
    """Test that place_structure successfully places a structure with rotation."""
    # Arrange
    structure = StructureData(
        name="village/plains/houses/small_house_1",
        position=Vec3iInput(coords=[10, 64, 10]),
        rotation=2  # 180 degrees
    )
    
    # Create a spy for the interface.placeStructure method
    place_structure_spy = MagicMock(return_value={"success": True})
    mock_interface.placeStructure = place_structure_spy
    
    # Patch the interface module
    with patch("src.gdmc_mcp.server.gdpc_interface", mock_interface):
        # Act
        result = await place_structure(structure, mock_context)
    
    # Assert
    assert result["success"] is True
    assert result["structure"] == "village/plains/houses/small_house_1"
    assert result["position"] == [10, 64, 10]
    assert result["rotation"] == 2
    
    # Verify the rotation was passed correctly
    place_structure_spy.assert_called_once()
    assert place_structure_spy.call_args[0][2] == 2  # Third positional argument (rotation)

@pytest.mark.asyncio
async def test_place_structure_with_mirror(mock_context, mock_editor, mock_interface):
    """Test that place_structure successfully places a structure with mirroring."""
    # Arrange
    structure = StructureData(
        name="village/plains/houses/small_house_1",
        position=Vec3iInput(coords=[10, 64, 10]),
        mirror=True
    )
    
    # Create a spy for the interface.placeStructure method
    place_structure_spy = MagicMock(return_value={"success": True})
    mock_interface.placeStructure = place_structure_spy
    
    # Patch the interface module
    with patch("src.gdmc_mcp.server.gdpc_interface", mock_interface):
        # Act
        result = await place_structure(structure, mock_context)
    
    # Assert
    assert result["success"] is True
    assert result["structure"] == "village/plains/houses/small_house_1"
    assert result["position"] == [10, 64, 10]
    assert result["mirror"] is True
    
    # Verify the mirror flag was passed correctly
    place_structure_spy.assert_called_once()
    assert place_structure_spy.call_args[0][3] is True  # Fourth positional argument (mirror)

@pytest.mark.asyncio
async def test_place_structure_with_rotation_and_mirror(mock_context, mock_editor, mock_interface):
    """Test that place_structure successfully places a structure with both rotation and mirroring."""
    # Arrange
    structure = StructureData(
        name="village/plains/houses/small_house_1",
        position=Vec3iInput(coords=[10, 64, 10]),
        rotation=1,  # 90 degrees
        mirror=True
    )
    
    # Create a spy for the interface.placeStructure method
    place_structure_spy = MagicMock(return_value={"success": True})
    mock_interface.placeStructure = place_structure_spy
    
    # Patch the interface module
    with patch("src.gdmc_mcp.server.gdpc_interface", mock_interface):
        # Act
        result = await place_structure(structure, mock_context)
    
    # Assert
    assert result["success"] is True
    assert result["structure"] == "village/plains/houses/small_house_1"
    assert result["position"] == [10, 64, 10]
    assert result["rotation"] == 1
    assert result["mirror"] is True
    
    # Verify both rotation and mirror were passed correctly
    place_structure_spy.assert_called_once()
    assert place_structure_spy.call_args[0][2] == 1  # Third positional argument (rotation)
    assert place_structure_spy.call_args[0][3] is True  # Fourth positional argument (mirror)

@pytest.mark.asyncio
async def test_place_structure_error_handling(mock_context, mock_interface):
    """Test that place_structure handles errors properly."""
    # Arrange
    structure = StructureData(
        name="village/plains/houses/small_house_1",
        position=Vec3iInput(coords=[10, 64, 10])
    )
    
    # Mock the interface to raise an exception
    mock_interface.placeStructure.side_effect = Exception("Test error")
    
    # Patch the interface module
    with patch("src.gdmc_mcp.server.gdpc_interface", mock_interface):
        # Act & Assert
        with pytest.raises(ValueError, match="Failed to place structure"):
            await place_structure(structure, mock_context)
    
    assert mock_context.error.called

@pytest.mark.asyncio
async def test_place_structure_missing_editor(mock_context, mock_interface):
    """Test that place_structure handles missing editor properly."""
    # Arrange
    structure = StructureData(
        name="village/plains/houses/small_house_1",
        position=Vec3iInput(coords=[10, 64, 10])
    )
    
    # Remove editor from context
    mock_context.request_context.lifespan_context = {}
    
    # Patch the interface module
    with patch("src.gdmc_mcp.server.gdpc_interface", mock_interface):
        # Act & Assert
        with pytest.raises(RuntimeError, match="GDPC Editor not found"):
            await place_structure(structure, mock_context)