# src/gdmc_mcp/models.py
"""
Pydantic models for the GDMC MCP API.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, field_validator
from pyglm.glm import ivec3
from typing_extensions import Annotated

class BlockData(BaseModel):
    """Block data model representing a Minecraft block."""
    id: str = Field(description="The namespaced ID of the block (e.g., 'minecraft:stone').")
    states: Optional[Dict[str, str]] = Field(None, description="Optional block states.")
    data: Optional[str] = Field(None, description="Optional SNBT block entity data string.")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary, excluding None values."""
        return {k: v for k, v in self.model_dump().items() if v is not None}
        
    def to_block(self) -> 'Block':
        """Convert to a GDPC Block object."""
        from gdpc import Block
        return Block(self.id, self.states, self.data)

class Vec3iInput(BaseModel):
    """3D integer vector input model."""
    coords: Annotated[List[int], Field(min_length=3, max_length=3)]

    @field_validator('coords')
    def check_length(cls, v):
        if len(v) != 3:
            raise ValueError('Position must have exactly 3 integer coordinates (X, Y, Z)')
        return v

    def to_ivec3(self) -> ivec3:
        """Convert to a pyGLM ivec3 object."""
        return ivec3(*self.coords)
    
    def to_tuple(self) -> Tuple[int, int, int]:
        """Convert to a tuple of 3 integers."""
        return tuple(self.coords)

class EntityData(BaseModel):
    """Entity data model representing a Minecraft entity."""
    id: str = Field(description="The namespaced ID of the entity (e.g., 'minecraft:zombie').")
    pos: Vec3iInput = Field(description="Position to place the entity at.")
    nbt: Optional[str] = Field(None, description="Optional SNBT entity data string.")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary, excluding None values."""
        result = {"id": self.id, "pos": self.pos.coords}
        if self.nbt:
            result["nbt"] = self.nbt
        return result

class StructureData(BaseModel):
    """Structure data model for Minecraft structures."""
    name: str = Field(description="The name of the structure (e.g., 'village/plains/houses/small_house_1').")
    position: Vec3iInput = Field(description="Position to place the structure at.")
    rotation: Optional[int] = Field(None, description="Rotation in 90-degree increments (0-3).")
    mirror: Optional[bool] = Field(None, description="Whether to mirror the structure.")
    integrity: Optional[float] = Field(None, ge=0.0, le=1.0, description="Structure integrity (0.0-1.0).")
    seed: Optional[int] = Field(None, description="Seed for random block replacement when integrity < 1.0.")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary, excluding None values."""
        result = {"name": self.name, "position": self.position.coords}
        if self.rotation is not None:
            result["rotation"] = self.rotation
        if self.mirror is not None:
            result["mirror"] = self.mirror
        if self.integrity is not None:
            result["integrity"] = self.integrity
        if self.seed is not None:
            result["seed"] = self.seed
        return result

class ChunkPosition(BaseModel):
    """Model representing a Minecraft chunk position."""
    x: int = Field(description="Chunk X coordinate.")
    z: int = Field(description="Chunk Z coordinate.")

class HeightmapData(BaseModel):
    """Model for heightmap data."""
    type: str = Field(description="Heightmap type (e.g., 'WORLD_SURFACE', 'MOTION_BLOCKING').")
    position: Optional[Vec3iInput] = Field(None, description="Optional position to get heightmap at.")
    chunk: Optional[ChunkPosition] = Field(None, description="Optional chunk position to get heightmap for.")
    
    @field_validator('type')
    def validate_heightmap_type(cls, v):
        valid_types = ["WORLD_SURFACE", "MOTION_BLOCKING", "MOTION_BLOCKING_NO_LEAVES", "OCEAN_FLOOR"]
        if v not in valid_types:
            raise ValueError(f"Heightmap type must be one of: {', '.join(valid_types)}")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary, excluding None values."""
        result = {"type": self.type}
        if self.position:
            result["position"] = self.position.coords
        if self.chunk:
            result["chunk"] = self.chunk.model_dump()
        return result

class TerrainAnalysisRequest(BaseModel):
    """Model for terrain analysis requests."""
    area: Optional[List[Vec3iInput]] = Field(None, description="Optional area to analyze (two corners).")
    analysis_types: List[str] = Field(
        ["heightmap", "biomes", "water", "trees"], 
        description="Types of analysis to perform."
    )
    
    @field_validator('area')
    def validate_area(cls, v):
        if v is not None and len(v) != 2:
            raise ValueError("Area must be defined by exactly 2 positions (corners)")
        return v
    
    @field_validator('analysis_types')
    def validate_analysis_types(cls, v):
        valid_types = ["heightmap", "biomes", "water", "trees", "ores", "caves", "structures"]
        for t in v:
            if t not in valid_types:
                raise ValueError(f"Analysis type '{t}' is not valid. Must be one of: {', '.join(valid_types)}")
        return v

class BuildConfig(BaseModel):
    """Configuration options for building structures."""
    adapt_to_terrain: bool = Field(True, description="Whether to adapt structures to the terrain.")
    clear_vegetation: bool = Field(True, description="Whether to clear vegetation before building.")
    add_lighting: bool = Field(True, description="Whether to add lighting to structures.")
    decorate_surroundings: bool = Field(False, description="Whether to decorate surroundings of structures.")
    replace_existing: bool = Field(True, description="Whether to replace existing blocks when building.")