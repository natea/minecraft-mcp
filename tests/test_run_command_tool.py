"""
Tests for the run_command tool in the GDMC MCP server.
"""
import sys
import os
from pathlib import Path
import pytest
from unittest.mock import patch, AsyncMock

# Add the project root to the Python path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.gdmc_mcp.server import run_command

@pytest.mark.asyncio
async def test_run_command_success(mock_context, mock_editor):
    """Test that run_command successfully executes a command."""
    # Arrange
    command = "say Hello, World!"
    
    # Act
    result = await run_command(command, mock_context)
    
    # Assert
    assert result["command"] == command
    assert len(result["results"]) > 0
    assert result["results"][0]["success"] is True
    assert "Executed command" in result["results"][0]["message"]
    assert mock_context.info.called

@pytest.mark.asyncio
async def test_run_command_complex(mock_context, mock_editor):
    """Test that run_command successfully executes a more complex command."""
    # Arrange
    command = "summon minecraft:zombie ~ ~ ~ {CustomName:'{\"text\":\"Test Zombie\"}'}"
    
    # Act
    result = await run_command(command, mock_context)
    
    # Assert
    assert result["command"] == command
    assert len(result["results"]) > 0
    assert result["results"][0]["success"] is True
    assert mock_context.info.called

@pytest.mark.asyncio
async def test_run_command_multiple_results(mock_context, mock_editor):
    """Test that run_command handles multiple command results."""
    # Arrange
    command = "execute as @a run say Hello"
    
    # Mock the editor to return multiple results
    mock_editor.runCommandGlobal = lambda cmd: [
        (True, "Player1 says: Hello"),
        (True, "Player2 says: Hello")
    ]
    
    # Act
    result = await run_command(command, mock_context)
    
    # Assert
    assert result["command"] == command
    assert len(result["results"]) == 2
    assert result["results"][0]["success"] is True
    assert result["results"][1]["success"] is True
    assert "Player1" in result["results"][0]["message"]
    assert "Player2" in result["results"][1]["message"]

@pytest.mark.asyncio
async def test_run_command_failed_command(mock_context, mock_editor):
    """Test that run_command handles failed commands."""
    # Arrange
    command = "invalid_command"
    
    # Mock the editor to return a failed command result
    mock_editor.runCommandGlobal = lambda cmd: [(False, "Unknown command: invalid_command")]
    
    # Act
    result = await run_command(command, mock_context)
    
    # Assert
    assert result["command"] == command
    assert len(result["results"]) == 1
    assert result["results"][0]["success"] is False
    assert "Unknown command" in result["results"][0]["message"]

@pytest.mark.asyncio
async def test_run_command_error_handling(mock_context, mock_editor):
    """Test that run_command handles errors properly."""
    # Arrange
    command = "say Hello, World!"
    
    # Create a custom mock editor that raises an exception
    def run_command_error(*args, **kwargs):
        raise Exception("Test error")
    
    # Replace the runCommandGlobal method with our error-raising version
    mock_editor.runCommandGlobal = run_command_error
    
    # Act & Assert
    with pytest.raises(ValueError, match="Failed to run command"):
        await run_command(command, mock_context)
    
    assert mock_context.error.called

@pytest.mark.asyncio
async def test_run_command_missing_editor(mock_context):
    """Test that run_command handles missing editor properly."""
    # Arrange
    command = "say Hello, World!"
    
    # Remove editor from context
    mock_context.request_context.lifespan_context = {}
    
    # Act & Assert
    with pytest.raises(RuntimeError, match="GDPC Editor not found"):
        await run_command(command, mock_context)