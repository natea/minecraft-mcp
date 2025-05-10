"""
Pytest configuration file for GDMC MCP server tests.
Contains fixtures for mocking the GDPC Editor and other dependencies.
"""
import sys
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastmcp import Context

# Add the project root to the Python path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Mock the GDPC modules
class MockBlock:
    """Mock implementation of GDPC Block class."""
    def __init__(self, id, states=None, data=None):
        self.id = id
        self.states = states or {}
        self.data = data
        
    def __str__(self):
        return f"Block({self.id})"
        
    def __repr__(self):
        return self.__str__()

class MockBox:
    """Mock implementation of GDPC Box class."""
    def __init__(self, offset=(0, 0, 0), size=(10, 10, 10)):
        self.offset = offset
        self.size = size
        self.end = tuple(o + s for o, s in zip(offset, size))

class MockWorldSlice:
    """Mock implementation of GDPC WorldSlice class."""
    def __init__(self):
        import numpy as np
        # Create mock heightmaps with numpy arrays
        self.heightmaps = {
            "WORLD_SURFACE": np.ones((1, 1), dtype=np.int32) * 64,
            "MOTION_BLOCKING": np.ones((1, 1), dtype=np.int32) * 63,
            "MOTION_BLOCKING_NO_LEAVES": np.ones((1, 1), dtype=np.int32) * 62,
            "OCEAN_FLOOR": np.ones((1, 1), dtype=np.int32) * 60
        }

# Don't inherit from Editor as it's too complex to mock properly
class MockEditor:
    """Mock implementation of GDPC Editor class."""
    def __init__(self, retries=1, timeout=10, buffering=True):
        self.retries = retries
        self.timeout = timeout
        self._buffering = buffering  # Use private attribute for property
        self.host = "localhost:9000"
        self._build_area = MockBox()
        self._blocks = {}  # Store blocks placed for verification
        
    @property
    def buffering(self):
        """Mock buffering property."""
        return self._buffering
        
    @buffering.setter
    def buffering(self, value):
        self._buffering = value
        
    def checkConnection(self):
        """Mock connection check."""
        return True
        
    def placeBlock(self, position, block):
        """Mock block placement."""
        pos_key = tuple(position)
        self._blocks[pos_key] = block
        return True
        
    def getBlockGlobal(self, position):
        """Mock get block."""
        pos_key = tuple(position)
        return self._blocks.get(pos_key, MockBlock("minecraft:air"))
        
    def getBiomeGlobal(self, position):
        """Mock get biome."""
        return "minecraft:plains"
        
    def getBuildArea(self):
        """Mock get build area."""
        return self._build_area
        
    def runCommandGlobal(self, command):
        """Mock run command."""
        return [(True, f"Executed command: {command}")]
        
    def flushBuffer(self):
        """Mock flush buffer."""
        return True
        
    def loadWorldSlice(self, rect):
        """Mock load world slice."""
        return MockWorldSlice()

# Mock the geometry module
class MockGeometry:
    """Mock implementation of GDPC geometry module."""
    @staticmethod
    def placeCuboid(editor, corner1, corner2, block):
        """Mock place cuboid."""
        # In a real implementation, this would place blocks at all positions in the cuboid
        return True
        
    @staticmethod
    def placeCuboidHollow(editor, corner1, corner2, block):
        """Mock place hollow cuboid."""
        # In a real implementation, this would place blocks at the shell of the cuboid
        return True

# Mock the interface module
class MockInterface:
    """Mock implementation of GDPC interface module."""
    @staticmethod
    def placeEntities(entity_data, host=None, retries=1, timeout=10):
        """Mock place entities."""
        return {"placed": len(entity_data)}
        
    @staticmethod
    def placeStructure(name, position, rotation=None, mirror=None, host=None, retries=1, timeout=10):
        """Mock place structure."""
        return {"success": True}
        
    @staticmethod
    def getPlayers(host=None, retries=1, timeout=10):
        """Mock get players."""
        return [{"name": "Player1", "uuid": "uuid1", "position": [0, 64, 0]}]
        
    @staticmethod
    def getEntities(host=None, retries=1, timeout=10):
        """Mock get entities."""
        return [{"id": "minecraft:zombie", "position": [10, 64, 10]}]
        
    @staticmethod
    def getVersion(host=None, retries=1, timeout=10):
        """Mock get version."""
        return "1.20.1"

@pytest.fixture
def mock_editor():
    """Fixture to provide a mock GDPC Editor instance."""
    return MockEditor()

@pytest.fixture
def mock_geometry():
    """Fixture to provide a mock GDPC geometry module."""
    return MockGeometry()

@pytest.fixture
def mock_interface():
    """Fixture to provide a mock GDPC interface module."""
    return MockInterface()

@pytest.fixture
def mock_context(mock_editor):
    """Fixture to provide a mock FastMCP Context with a mock editor in the lifespan context."""
    context = MagicMock(spec=Context)
    
    # Create a proper nested structure
    request_context = MagicMock()
    lifespan_context = {"editor": mock_editor}
    request_context.lifespan_context = lifespan_context
    context.request_context = request_context
    
    # Make info and error methods async
    context.info = AsyncMock()
    context.error = AsyncMock()
    context.warning = AsyncMock()
    
    # Add a helper method to verify the editor is properly set
    context.get_editor = lambda: context.request_context.lifespan_context.get("editor")
    
    return context