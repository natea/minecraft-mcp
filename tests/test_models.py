"""
Tests for the data models in the GDMC MCP server.
"""
import sys
import os
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add the project root to the Python path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.gdmc_mcp.models import (
    BlockData,
    Vec3iInput,
    EntityData,
    StructureData,
    ChunkPosition,
    HeightmapData,
    TerrainAnalysisRequest,
    BuildConfig
)

class TestBlockData:
    """Tests for the BlockData model."""
    
    def test_block_data_basic(self):
        """Test basic BlockData creation."""
        block = BlockData(id="minecraft:stone")
        assert block.id == "minecraft:stone"
        assert block.states is None
        assert block.data is None
    
    def test_block_data_with_states(self):
        """Test BlockData with states."""
        states = {"facing": "north", "half": "bottom"}
        block = BlockData(id="minecraft:oak_stairs", states=states)
        assert block.id == "minecraft:oak_stairs"
        assert block.states == states
        assert block.data is None
    
    def test_block_data_with_data(self):
        """Test BlockData with data."""
        data = '{"Items":[{"id":"minecraft:diamond","Count":64,"Slot":0}]}'
        block = BlockData(id="minecraft:chest", data=data)
        assert block.id == "minecraft:chest"
        assert block.states is None
        assert block.data == data
    
    def test_block_data_to_dict(self):
        """Test BlockData to_dict method."""
        block = BlockData(id="minecraft:stone", states={"variant": "granite"})
        result = block.to_dict()
        assert result == {"id": "minecraft:stone", "states": {"variant": "granite"}}
    
    def test_block_data_to_block(self):
        """Test BlockData to_block method."""
        # Mock the Block class
        mock_block = MagicMock()
        with patch("gdpc.Block", return_value=mock_block) as mock_block_class:
            block_data = BlockData(id="minecraft:stone", states={"variant": "granite"})
            result = block_data.to_block()
            
            # Verify Block was created with correct parameters
            mock_block_class.assert_called_once_with(
                "minecraft:stone",
                {"variant": "granite"},
                None
            )
            assert result == mock_block

class TestVec3iInput:
    """Tests for the Vec3iInput model."""
    
    def test_vec3i_input_basic(self):
        """Test basic Vec3iInput creation."""
        vec = Vec3iInput(coords=[10, 20, 30])
        assert vec.coords == [10, 20, 30]
    
    def test_vec3i_input_validation(self):
        """Test Vec3iInput validation."""
        # Should fail with wrong length
        with pytest.raises(ValueError):
            Vec3iInput(coords=[10, 20])
        
        with pytest.raises(ValueError):
            Vec3iInput(coords=[10, 20, 30, 40])
    
    def test_vec3i_input_to_ivec3(self):
        """Test Vec3iInput to_ivec3 method."""
        vec = Vec3iInput(coords=[10, 20, 30])
        result = vec.to_ivec3()
        # Check that it's an ivec3 with correct values
        assert result.x == 10
        assert result.y == 20
        assert result.z == 30
    
    def test_vec3i_input_to_tuple(self):
        """Test Vec3iInput to_tuple method."""
        vec = Vec3iInput(coords=[10, 20, 30])
        result = vec.to_tuple()
        assert result == (10, 20, 30)

class TestEntityData:
    """Tests for the EntityData model."""
    
    def test_entity_data_basic(self):
        """Test basic EntityData creation."""
        entity = EntityData(
            id="minecraft:zombie",
            pos=Vec3iInput(coords=[10, 64, 10])
        )
        assert entity.id == "minecraft:zombie"
        assert entity.pos.coords == [10, 64, 10]
        assert entity.nbt is None
    
    def test_entity_data_with_nbt(self):
        """Test EntityData with NBT data."""
        nbt = "{CustomName:'{\"text\":\"Test Zombie\"}',Invulnerable:1b}"
        entity = EntityData(
            id="minecraft:zombie",
            pos=Vec3iInput(coords=[10, 64, 10]),
            nbt=nbt
        )
        assert entity.id == "minecraft:zombie"
        assert entity.pos.coords == [10, 64, 10]
        assert entity.nbt == nbt
    
    def test_entity_data_to_dict(self):
        """Test EntityData to_dict method."""
        entity = EntityData(
            id="minecraft:zombie",
            pos=Vec3iInput(coords=[10, 64, 10]),
            nbt="{CustomName:'{\"text\":\"Test Zombie\"}'}"
        )
        result = entity.to_dict()
        assert result["id"] == "minecraft:zombie"
        assert result["pos"] == [10, 64, 10]
        assert "nbt" in result

class TestStructureData:
    """Tests for the StructureData model."""
    
    def test_structure_data_basic(self):
        """Test basic StructureData creation."""
        structure = StructureData(
            name="village/plains/houses/small_house_1",
            position=Vec3iInput(coords=[10, 64, 10])
        )
        assert structure.name == "village/plains/houses/small_house_1"
        assert structure.position.coords == [10, 64, 10]
        assert structure.rotation is None
        assert structure.mirror is None
    
    def test_structure_data_with_options(self):
        """Test StructureData with rotation and mirror."""
        structure = StructureData(
            name="village/plains/houses/small_house_1",
            position=Vec3iInput(coords=[10, 64, 10]),
            rotation=2,
            mirror=True
        )
        assert structure.name == "village/plains/houses/small_house_1"
        assert structure.position.coords == [10, 64, 10]
        assert structure.rotation == 2
        assert structure.mirror is True
    
    def test_structure_data_to_dict(self):
        """Test StructureData to_dict method."""
        structure = StructureData(
            name="village/plains/houses/small_house_1",
            position=Vec3iInput(coords=[10, 64, 10]),
            rotation=2,
            mirror=True
        )
        result = structure.to_dict()
        assert result["name"] == "village/plains/houses/small_house_1"
        assert result["position"] == [10, 64, 10]
        assert result["rotation"] == 2
        assert result["mirror"] is True

class TestHeightmapData:
    """Tests for the HeightmapData model."""
    
    def test_heightmap_data_basic(self):
        """Test basic HeightmapData creation."""
        heightmap = HeightmapData(type="WORLD_SURFACE")
        assert heightmap.type == "WORLD_SURFACE"
        assert heightmap.position is None
        assert heightmap.chunk is None
    
    def test_heightmap_data_with_position(self):
        """Test HeightmapData with position."""
        heightmap = HeightmapData(
            type="WORLD_SURFACE",
            position=Vec3iInput(coords=[10, 0, 10])
        )
        assert heightmap.type == "WORLD_SURFACE"
        assert heightmap.position.coords == [10, 0, 10]
        assert heightmap.chunk is None
    
    def test_heightmap_data_with_chunk(self):
        """Test HeightmapData with chunk position."""
        heightmap = HeightmapData(
            type="WORLD_SURFACE",
            chunk=ChunkPosition(x=0, z=0)
        )
        assert heightmap.type == "WORLD_SURFACE"
        assert heightmap.position is None
        assert heightmap.chunk.x == 0
        assert heightmap.chunk.z == 0
    
    def test_heightmap_data_invalid_type(self):
        """Test HeightmapData with invalid type."""
        with pytest.raises(ValueError):
            HeightmapData(type="INVALID_TYPE")
    
    def test_heightmap_data_to_dict(self):
        """Test HeightmapData to_dict method."""
        heightmap = HeightmapData(
            type="WORLD_SURFACE",
            position=Vec3iInput(coords=[10, 0, 10])
        )
        result = heightmap.to_dict()
        assert result["type"] == "WORLD_SURFACE"
        assert result["position"] == [10, 0, 10]

class TestTerrainAnalysisRequest:
    """Tests for the TerrainAnalysisRequest model."""
    
    def test_terrain_analysis_request_basic(self):
        """Test basic TerrainAnalysisRequest creation."""
        request = TerrainAnalysisRequest()
        assert request.area is None
        assert request.analysis_types == ["heightmap", "biomes", "water", "trees"]
    
    def test_terrain_analysis_request_with_area(self):
        """Test TerrainAnalysisRequest with area."""
        request = TerrainAnalysisRequest(
            area=[
                Vec3iInput(coords=[0, 0, 0]),
                Vec3iInput(coords=[100, 100, 100])
            ]
        )
        assert len(request.area) == 2
        assert request.area[0].coords == [0, 0, 0]
        assert request.area[1].coords == [100, 100, 100]
    
    def test_terrain_analysis_request_invalid_area(self):
        """Test TerrainAnalysisRequest with invalid area."""
        with pytest.raises(ValueError):
            TerrainAnalysisRequest(
                area=[Vec3iInput(coords=[0, 0, 0])]  # Only one corner
            )
    
    def test_terrain_analysis_request_invalid_type(self):
        """Test TerrainAnalysisRequest with invalid analysis type."""
        with pytest.raises(ValueError):
            TerrainAnalysisRequest(analysis_types=["invalid_type"])

class TestBuildConfig:
    """Tests for the BuildConfig model."""
    
    def test_build_config_defaults(self):
        """Test BuildConfig default values."""
        config = BuildConfig()
        assert config.adapt_to_terrain is True
        assert config.clear_vegetation is True
        assert config.add_lighting is True
        assert config.decorate_surroundings is False
        assert config.replace_existing is True
    
    def test_build_config_custom(self):
        """Test BuildConfig with custom values."""
        config = BuildConfig(
            adapt_to_terrain=False,
            clear_vegetation=False,
            add_lighting=False,
            decorate_surroundings=True,
            replace_existing=False
        )
        assert config.adapt_to_terrain is False
        assert config.clear_vegetation is False
        assert config.add_lighting is False
        assert config.decorate_surroundings is True
        assert config.replace_existing is False