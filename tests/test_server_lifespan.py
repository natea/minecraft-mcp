"""
Tests for the server lifespan and utility functions in the GDMC MCP server.
"""
import sys
import os
from pathlib import Path
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from contextlib import asynccontextmanager

# Add the project root to the Python path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gdpc.exceptions import InterfaceConnectionError, BuildAreaNotSetError
from src.gdmc_mcp.server import lifespan, _get_editor

@pytest.mark.asyncio
async def test_lifespan_success():
    """Test that lifespan successfully initializes and cleans up the GDPC Editor."""
    # Arrange
    mock_server = MagicMock()
    mock_editor = MagicMock()
    
    # Mock anyio.to_thread.run_sync to return our mock editor
    async def mock_run_sync(func, *args, **kwargs):
        if "lambda" in str(func):  # This is a bit hacky but works for our test
            return mock_editor
        return None
    
    # Act
    with patch("src.gdmc_mcp.server.anyio.to_thread.run_sync", mock_run_sync):
        async with lifespan(mock_server) as context:
            # Assert during lifespan
            assert "editor" in context
            assert context["editor"] == mock_editor
            assert mock_editor.checkConnection.called
    
    # Assert after lifespan
    assert mock_editor.flushBuffer.called

@pytest.mark.asyncio
async def test_lifespan_connection_error():
    """Test that lifespan handles connection errors properly."""
    # Arrange
    mock_server = MagicMock()
    
    # Mock anyio.to_thread.run_sync to raise InterfaceConnectionError
    async def mock_run_sync(func, *args, **kwargs):
        if "checkConnection" in str(func):
            raise InterfaceConnectionError("Connection failed")
        return MagicMock()  # Return a mock for the editor creation
    
    # Act & Assert
    with patch("src.gdmc_mcp.server.anyio.to_thread.run_sync", mock_run_sync):
        with pytest.raises(RuntimeError, match="Failed to connect to GDMC HTTP interface"):
            async with lifespan(mock_server) as context:
                pass  # Should not reach here

@pytest.mark.asyncio
async def test_lifespan_general_error():
    """Test that lifespan handles general errors properly."""
    # Arrange
    mock_server = MagicMock()
    
    # Mock anyio.to_thread.run_sync to raise a general exception
    async def mock_run_sync(func, *args, **kwargs):
        if "lambda" in str(func):  # During editor creation
            raise Exception("General error")
        return None
    
    # Act & Assert
    with patch("src.gdmc_mcp.server.anyio.to_thread.run_sync", mock_run_sync):
        with pytest.raises(RuntimeError, match="Failed to initialize GDPC Editor"):
            async with lifespan(mock_server) as context:
                pass  # Should not reach here

@pytest.mark.asyncio
async def test_lifespan_flush_error():
    """Test that lifespan handles errors during buffer flush."""
    # Arrange
    mock_server = MagicMock()
    mock_editor = MagicMock()
    
    # Mock anyio.to_thread.run_sync with different behaviors
    call_count = 0
    async def mock_run_sync(func, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:  # First two calls (editor creation and connection check)
            return mock_editor
        else:  # Third call (buffer flush)
            raise Exception("Flush error")
    
    # Act
    with patch("src.gdmc_mcp.server.anyio.to_thread.run_sync", mock_run_sync):
        # Should not raise exception even if flush fails
        async with lifespan(mock_server) as context:
            assert "editor" in context
            assert context["editor"] == mock_editor

def test_get_editor_success(mock_context, mock_editor):
    """Test that _get_editor successfully retrieves the editor from context."""
    # Act
    editor = _get_editor(mock_context)
    
    # Assert
    assert editor == mock_editor

def test_get_editor_missing(mock_context):
    """Test that _get_editor handles missing editor properly."""
    # Arrange
    mock_context.request_context.lifespan_context = {}  # Empty context
    
    # Act & Assert
    with pytest.raises(RuntimeError, match="GDPC Editor not found"):
        _get_editor(mock_context)

def test_get_editor_wrong_type(mock_context):
    """Test that _get_editor handles wrong editor type properly."""
    # Arrange
    mock_context.request_context.lifespan_context = {"editor": "not an editor"}
    
    # Act & Assert
    with pytest.raises(RuntimeError, match="GDPC Editor not found"):
        _get_editor(mock_context)

def test_get_editor_no_context():
    """Test that _get_editor handles missing context properly."""
    # Arrange
    context = MagicMock()
    # Remove the nested attributes to cause AttributeError
    del context.request_context
    
    # Act & Assert
    with pytest.raises(RuntimeError, match="GDPC Editor context is not available"):
        _get_editor(context)