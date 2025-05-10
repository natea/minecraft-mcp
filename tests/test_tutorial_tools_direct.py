"""
Direct test for the tutorial_build_village function to verify our fix.
This bypasses the client-server architecture and tests the function directly.
"""

import asyncio
import sys
import os
from pathlib import Path
import inspect
from unittest.mock import patch
import pytest

from gdpc import Editor
from src.gdmc_mcp.tutorial_tools import build_example_village

# Mock asyncio.to_thread.run_sync
async def mock_run_sync(func, *args, **kwargs):
    """Mock implementation of asyncio.to_thread.run_sync that runs the function directly."""
    if inspect.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    return func(*args, **kwargs)

class MockContext:
    """Mock context object to simulate the request context."""
    
    class MockRequestContext:
        """Mock request context with lifespan context."""
        
        def __init__(self, editor):
            self.lifespan_context = {"editor": editor}
            
        def get(self, key, default=None):
            """Get a value from the lifespan context."""
            return self.lifespan_context.get(key, default)
    
    def __init__(self, editor):
        self.request_context = self.MockRequestContext(editor)

@pytest.mark.asyncio
async def test_build_example_village_none_position():
    """Test the tutorial_build_village function directly with None position."""
    print("Testing tutorial_build_village function with context handling...")
    
    # Create a mock editor
    class MockEditor:
        """Mock Editor that logs calls instead of connecting to Minecraft."""
        
        def __init__(self):
            self.calls = []
            self.buffering = False
            
        def getBuildArea(self):
            """Mock getBuildArea method."""
            self.calls.append(("getBuildArea",))
            from gdpc.vector_tools import Box, ivec3
            return Box(ivec3(0, 60, 0), ivec3(100, 100, 100))
            
        def placeBlock(self, pos, block):
            """Mock placeBlock method."""
            self.calls.append(("placeBlock", pos, block))
            return True
            
        def flushBuffer(self):
            """Mock flushBuffer method."""
            self.calls.append(("flushBuffer",))
            return True
            
        def loadWorldSlice(self, rect, cache=False):
            """Mock loadWorldSlice method."""
            self.calls.append(("loadWorldSlice", rect, cache))
            # Create a minimal mock world slice
            class MockWorldSlice:
                def __init__(self):
                    from numpy import zeros
                    self.heightmaps = {
                        "MOTION_BLOCKING": zeros((100, 100), dtype=int) + 65
                    }
            return MockWorldSlice()
    
    editor = MockEditor()
    
    # Patch asyncio.to_thread.run_sync with our mock implementation
    with patch('anyio.to_thread.run_sync', mock_run_sync):
        # Test with None position (should use default position finding)
        print("\nTest 1: Calling build_example_village with None position")
        # Mock the find_build_position function to return a simple position
        with patch('src.gdmc_mcp.gdpc_utils.find_build_position',
                  return_value=((0, 65, 0), 65)):
            result = await build_example_village(
                editor,
                position=None,
                num_houses=3
            )
        assert isinstance(result, dict)
        assert result.get("houses") is not None
        assert len(editor.calls) > 0

@pytest.mark.asyncio
async def test_build_example_village_specific_position():
    """Test the tutorial_build_village function directly with specific position."""
    class MockEditor:
        """Mock Editor that logs calls instead of connecting to Minecraft."""
        
        def __init__(self):
            self.calls = []
            self.buffering = False
            
        def getBuildArea(self):
            """Mock getBuildArea method."""
            self.calls.append(("getBuildArea",))
            from gdpc.vector_tools import Box, ivec3
            return Box(ivec3(0, 60, 0), ivec3(100, 100, 100))
            
        def placeBlock(self, pos, block):
            """Mock placeBlock method."""
            self.calls.append(("placeBlock", pos, block))
            return True
            
        def flushBuffer(self):
            """Mock flushBuffer method."""
            self.calls.append(("flushBuffer",))
            return True
            
        def loadWorldSlice(self, rect, cache=False):
            """Mock loadWorldSlice method."""
            self.calls.append(("loadWorldSlice", rect, cache))
            # Create a minimal mock world slice
            class MockWorldSlice:
                def __init__(self):
                    from numpy import zeros
                    self.heightmaps = {
                        "MOTION_BLOCKING": zeros((100, 100), dtype=int) + 65
                    }
            return MockWorldSlice()
    
    editor = MockEditor()
    
    # Patch asyncio.to_thread.run_sync with our mock implementation
    with patch('anyio.to_thread.run_sync', mock_run_sync):
        # Test with specific position
        print("\nTest 2: Calling build_example_village with specific position")
        editor.calls = []  # Reset call log
        # Mock the generate_village function to return a simple result
        with patch('src.gdmc_mcp.gdpc_utils.generate_village',
                  return_value={"houses": 3, "position": [0, 65, 0]}):
            result = await build_example_village(
                editor,
                position=(0, 65, 0),
                num_houses=3
            )
        assert isinstance(result, dict)
        assert result.get("houses") is not None
        assert len(editor.calls) > 0