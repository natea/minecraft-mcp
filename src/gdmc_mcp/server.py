# src/gdmc_mcp/server.py
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, cast

import anyio
from gdpc import Editor, Block, Box
from gdpc import interface as gdpc_interface # Use gdpc's interface module directly for some actions
from gdpc.exceptions import InterfaceConnectionError, BuildAreaNotSetError
from gdpc.vector_tools import Vec3iLike, ivec3 # Import ivec3 for explicit casting
from pydantic import Field
from typing_extensions import Annotated

from fastmcp import FastMCP, Context

# Import our models
from .models import BlockData, Vec3iInput, EntityData, StructureData

# Import utility functions and tutorial tools
from .gdpc_utils import find_build_position, analyze_terrain
from .tutorial_tools import register_tutorial_tools

# Configure logging for GDPC (optional, but good practice)
logging.basicConfig(level=logging.INFO)
gdpc_logger = logging.getLogger("gdpc")
gdpc_logger.setLevel(logging.WARNING) # Adjust level as needed

logger = logging.getLogger(__name__)

# Lifespan context manager to manage the GDPC Editor instance
@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """Create and manage the GDPC Editor instance."""
    editor = None
    try:
        # Initialize the editor - consider making buffering configurable via settings
        logger.info("Initializing GDPC Editor...")
        # Run synchronous Editor creation in a thread to avoid blocking asyncio loop
        # Create Editor with parameters first, then pass the function to run_sync
        editor = await anyio.to_thread.run_sync(lambda: Editor(retries=2, timeout=10, buffering=False))
        # Check connection immediately
        await anyio.to_thread.run_sync(lambda: editor.checkConnection())
        logger.info("GDPC Editor connection successful.")
        yield {"editor": editor}
    except InterfaceConnectionError as e:
        logger.error(f"Fatal: Could not connect to GDMC HTTP interface: {e}")
        # If connection fails on startup, we might want to prevent the server from running fully.
        # Raising an exception here will stop the server lifespan.
        raise RuntimeError(f"Failed to connect to GDMC HTTP interface: {e}") from e
    except Exception as e:
        logger.error(f"Fatal: Error initializing GDPC Editor: {e}", exc_info=True)
        raise RuntimeError(f"Failed to initialize GDPC Editor: {e}") from e
    finally:
        if editor is not None:
            logger.info("Shutting down GDPC Editor (flushing buffer)...")
            # Ensure buffer is flushed on shutdown
            try:
                await anyio.to_thread.run_sync(lambda: editor.flushBuffer())
                logger.info("GDPC Editor buffer flushed.")
            except Exception as e:
                logger.error(f"Error flushing GDPC buffer on shutdown: {e}", exc_info=True)
            # If using multithreading, might need editor.awaitBufferFlushes() here


# Create the FastMCP server instance
mcp = FastMCP(
    name="GDMC Bridge",
    instructions="Provides tools and resources to interact with a Minecraft world via GDPC.",
    lifespan=lifespan,
    # Add gdpc as a dependency for `fastmcp install`
    dependencies=["gdpc>=8.1.0"]
)


# Helper to get the editor instance from context
def _get_editor(ctx: Context) -> Editor:
    """Retrieves the GDPC Editor instance from the lifespan context."""
    try:
        editor = ctx.request_context.lifespan_context.get("editor")
        if editor is None:
            raise RuntimeError("GDPC Editor not found in lifespan context.")
        # Allow MockEditor in tests
        if 'MockEditor' in editor.__class__.__name__ or isinstance(editor, Editor):
            return editor
        raise RuntimeError(f"Invalid editor type: {type(editor)}")
    except AttributeError as e:
         # This can happen if context is accessed outside a request
        raise RuntimeError("GDPC Editor context is not available.") from e


# === TOOLS ===

@mcp.tool()
async def place_block(
    position: Annotated[Vec3iInput, Field(description="List of [X, Y, Z] coordinates.")],
    block: Annotated[BlockData, Field(description="Block ID and optional states/data.")],
    ctx: Context
) -> dict[str, Any]:
    """Places a block at the specified position."""
    editor = _get_editor(ctx)
    pos_vec = position.to_ivec3()
    block_obj = block.to_block()
    await ctx.info(f"Placing block {block_obj} at {tuple(pos_vec)}")
    try:
        # Run synchronous placeBlock in a thread
        success = await anyio.to_thread.run_sync(lambda: editor.placeBlock(pos_vec, block_obj))
        # Ensure we return the string representation in the format "Block(minecraft:stone)"
        block_str = f"Block({block_obj.id})" if not str(block_obj).startswith("Block(") else str(block_obj)
        return {"success": success, "position": list(pos_vec), "block": block_str}
    except Exception as e:
        await ctx.error(f"Error placing block: {e}")
        raise ValueError(f"Failed to place block: {e}") from e

@mcp.tool()
async def run_command(
    command: Annotated[str, Field(description="Minecraft command without leading '/'.")],
    ctx: Context
) -> dict[str, Any]:
    """Runs a Minecraft command on the server."""
    editor = _get_editor(ctx)
    await ctx.info(f"Running command: {command}")
    try:
        # Run synchronous runCommand in a thread
        results = await anyio.to_thread.run_sync(lambda: editor.runCommandGlobal(command)) # Using Global to avoid transform issues for now
        # Process results: list of (success, message/None) tuples
        processed_results = [{"success": r[0], "message": r[1]} for r in results]
        return {"command": command, "results": processed_results}
    except Exception as e:
        await ctx.error(f"Error running command: {e}")
        raise ValueError(f"Failed to run command: {e}") from e

@mcp.tool()
async def place_cuboid(
    corner1: Annotated[Vec3iInput, Field(description="First corner [X, Y, Z].")],
    corner2: Annotated[Vec3iInput, Field(description="Second corner [X, Y, Z].")],
    block: Annotated[BlockData, Field(description="Block ID and optional states/data.")],
    hollow: Annotated[bool, Field(description="Whether to place only the shell.", default=False)],
    ctx: Context
) -> dict[str, Any]:
    """Places a solid or hollow cuboid."""
    from gdpc import geometry # Import here as it's less common

    editor = _get_editor(ctx)
    c1 = corner1.to_ivec3()
    c2 = corner2.to_ivec3()
    block_obj = block.to_block()
    shape_type = "hollow cuboid" if hollow else "solid cuboid"
    await ctx.info(f"Placing {shape_type} of {block_obj} between {tuple(c1)} and {tuple(c2)}")
    try:
        if hollow:
            await anyio.to_thread.run_sync(lambda: geometry.placeCuboidHollow(editor, c1, c2, block_obj))
        else:
            await anyio.to_thread.run_sync(lambda: geometry.placeCuboid(editor, c1, c2, block_obj))
        return {"success": True, "corner1": list(c1), "corner2": list(c2), "block": str(block_obj), "hollow": hollow}
    except Exception as e:
        await ctx.error(f"Error placing cuboid: {e}")
        raise ValueError(f"Failed to place cuboid: {e}") from e

@mcp.tool()
async def place_entities(
    entities: Annotated[list[EntityData], Field(
        description="List of entities to place.", 
        min_length=1, 
        max_length=50
    )],
    ctx: Context
) -> dict[str, Any]:
    """Places multiple entities at specified positions with optional NBT data."""
    editor = _get_editor(ctx)
    
    await ctx.info(f"Placing {len(entities)} entities...")
    
    try:
        entity_data = []
        for entity in entities:
            pos = entity.pos.to_ivec3()
            # Create entity data with the correct format for gdpc_interface.placeEntities
            entity_dict = {
                "id": entity.id,
                "x": float(pos.x),
                "y": float(pos.y),
                "z": float(pos.z)
            }
            
            # Add NBT data if provided
            if entity.nbt:
                entity_dict["nbt"] = entity.nbt
                
            entity_data.append(entity_dict)
        
        # Using the interface directly for placing entities
        # The position parameter is required and acts as a reference point for relative coordinates
        # We'll use (0,0,0) as the reference point since our entity positions are already absolute
        result = await anyio.to_thread.run_sync(
            lambda: gdpc_interface.placeEntities(
                entity_data,
                position=(0, 0, 0),  # Reference position for relative coordinates
                host=editor.host,
                retries=editor.retries,
                timeout=editor.timeout
            )
        )
        
        return {
            "success": True,
            "placed": len(entities),
            "result": result
        }
    except Exception as e:
        await ctx.error(f"Error placing entities: {e}")
        raise ValueError(f"Failed to place entities: {e}") from e

@mcp.tool()
async def place_structure(
    structure: Annotated[StructureData, Field(description="Structure to place.")],
    ctx: Context
) -> dict[str, Any]:
    """Places a Minecraft structure at the specified position with optional rotation and mirroring."""
    editor = _get_editor(ctx)
    
    pos = structure.position.to_ivec3()
    await ctx.info(f"Placing structure {structure.name} at {tuple(pos)}...")
    
    try:
        # Using the interface directly for placing structures
        result = await anyio.to_thread.run_sync(
            lambda: gdpc_interface.placeStructure(
                structure.name,
                (pos.x, pos.y, pos.z),
                structure.rotation,
                structure.mirror,
                host=editor.host,
                retries=editor.retries,
                timeout=editor.timeout
            )
        )
        
        return {
            "success": True,
            "structure": structure.name,
            "position": list(pos),
            "rotation": structure.rotation,
            "mirror": structure.mirror,
            "result": result
        }
    except Exception as e:
        await ctx.error(f"Error placing structure: {e}")
        raise ValueError(f"Failed to place structure: {e}") from e


# === RESOURCES ===

@mcp.resource(uri="gdmc://build_area", description="Get the currently set build area.")
async def get_build_area(ctx: Context) -> dict[str, list[int]]:
    """Retrieves the build area."""
    editor = _get_editor(ctx)
    await ctx.info("Retrieving build area...")
    try:
        # Run synchronous getBuildArea in a thread
        build_area_box: Box = await anyio.to_thread.run_sync(lambda: editor.getBuildArea())
        # Convert Box to a serializable dict
        return {
            "offset": list(build_area_box.offset),
            "size": list(build_area_box.size),
            "end": list(build_area_box.end)
        }
    except BuildAreaNotSetError:
        await ctx.warning("Build area not set.")
        raise ValueError("Build area is not set in Minecraft. Use /setbuildarea.") from None
    except Exception as e:
        await ctx.error(f"Error getting build area: {e}")
        raise ValueError(f"Failed to get build area: {e}") from e

@mcp.resource(uri="gdmc://players", description="Get information about players on the server.")
async def get_players(ctx: Context) -> list[dict[str, Any]]:
    """Retrieves information about online players."""
    editor = _get_editor(ctx)
    await ctx.info("Retrieving player data...")
    try:
        # gdpc_interface functions are synchronous network calls
        player_data = await anyio.to_thread.run_sync(
            lambda: gdpc_interface.getPlayers(
                host=editor.host,
                retries=editor.retries,
                timeout=editor.timeout
            )
        )
        return cast(list[dict[str, Any]], player_data) # Ensure correct type cast
    except Exception as e:
        await ctx.error(f"Error getting player data: {e}")
        raise ValueError(f"Failed to get player data: {e}") from e

@mcp.resource(uri="gdmc://entities", description="Get information about entities in the world.")
async def get_entities(ctx: Context) -> list[dict[str, Any]]:
    """Retrieves information about entities in the world."""
    editor = _get_editor(ctx)
    await ctx.info("Retrieving entity data...")
    try:
        # gdpc_interface functions are synchronous network calls
        entity_data = await anyio.to_thread.run_sync(
            lambda: gdpc_interface.getEntities(
                host=editor.host,
                retries=editor.retries,
                timeout=editor.timeout
            )
        )
        return cast(list[dict[str, Any]], entity_data) # Ensure correct type cast
    except Exception as e:
        await ctx.error(f"Error getting entity data: {e}")
        raise ValueError(f"Failed to get entity data: {e}") from e

@mcp.resource(uri="gdmc://minecraft_version", description="Get the Minecraft server version.")
async def get_minecraft_version(ctx: Context) -> dict[str, str]:
    """Retrieves the Minecraft version reported by the GDMC HTTP interface."""
    editor = _get_editor(ctx)
    await ctx.info("Retrieving Minecraft version...")
    try:
        # gdpc_interface functions are synchronous network calls
        version = await anyio.to_thread.run_sync(
            lambda: gdpc_interface.getVersion(
                host=editor.host,
                retries=editor.retries,
                timeout=editor.timeout
            )
        )
        return {"version": version}
    except Exception as e:
        await ctx.error(f"Error getting Minecraft version: {e}")
        raise ValueError(f"Failed to get Minecraft version: {e}") from e

@mcp.resource(uri="gdmc://heightmaps", description="Get available heightmap types.")
async def get_heightmap_types(ctx: Context) -> dict[str, list[str]]:
    """Retrieves the available heightmap types."""
    await ctx.info("Retrieving heightmap types...")
    try:
        # These are the standard heightmap types in Minecraft
        heightmap_types = [
            "WORLD_SURFACE",
            "MOTION_BLOCKING",
            "MOTION_BLOCKING_NO_LEAVES",
            "OCEAN_FLOOR"
        ]
        return {"heightmap_types": heightmap_types}
    except Exception as e:
        await ctx.error(f"Error getting heightmap types: {e}")
        raise ValueError(f"Failed to get heightmap types: {e}") from e


# === RESOURCE TEMPLATES ===

@mcp.resource(uri="gdmc://block/{x}/{y}/{z}", description="Get the block at a specific coordinate.")
async def get_block(
    x: Annotated[int, Field(description="X coordinate")],
    y: Annotated[int, Field(description="Y coordinate")],
    z: Annotated[int, Field(description="Z coordinate")],
    ctx: Context
) -> dict[str, Any]:
    """Retrieves the block data at the given global coordinates."""
    editor = _get_editor(ctx)
    pos = ivec3(x, y, z)
    await ctx.info(f"Getting block at {tuple(pos)}")
    try:
        # Run synchronous getBlockGlobal in a thread
        block_obj: Block = await anyio.to_thread.run_sync(editor.getBlockGlobal, pos)
        if block_obj.id == "minecraft:void_air":
            raise ValueError(f"Coordinates {tuple(pos)} are outside the loaded world.")
        # Convert Block to a serializable dict
        return {"id": block_obj.id, "states": block_obj.states, "data": block_obj.data}
    except Exception as e:
        await ctx.error(f"Error getting block at {tuple(pos)}: {e}")
        raise ValueError(f"Failed to get block at {tuple(pos)}: {e}") from e

@mcp.resource(uri="gdmc://biome/{x}/{y}/{z}", description="Get the biome ID at a specific coordinate.")
async def get_biome(
    x: Annotated[int, Field(description="X coordinate")],
    y: Annotated[int, Field(description="Y coordinate")],
    z: Annotated[int, Field(description="Z coordinate")],
    ctx: Context
) -> dict[str, str | list[int]]:
    """Retrieves the biome ID at the given global coordinates."""
    editor = _get_editor(ctx)
    pos = ivec3(x, y, z)
    await ctx.info(f"Getting biome at {tuple(pos)}")
    try:
        # Run synchronous getBiomeGlobal in a thread
        biome_id: str = await anyio.to_thread.run_sync(editor.getBiomeGlobal, pos)
        if not biome_id:
             raise ValueError(f"Coordinates {tuple(pos)} are outside the loaded world or have no biome.")
        return {"biome_id": biome_id, "position": list(pos)}
    except Exception as e:
        await ctx.error(f"Error getting biome at {tuple(pos)}: {e}")
        raise ValueError(f"Failed to get biome at {tuple(pos)}: {e}") from e

@mcp.resource(uri="gdmc://heightmap/{type}/{x}/{z}", description="Get the height at a specific coordinate.")
async def get_height(
    type: Annotated[str, Field(description="Heightmap type")],
    x: Annotated[int, Field(description="X coordinate")],
    z: Annotated[int, Field(description="Z coordinate")],
    ctx: Context
) -> dict[str, Any]:
    """Retrieves the height at the given global coordinates using the specified heightmap type."""
    editor = _get_editor(ctx)
    await ctx.info(f"Getting height at ({x},{z}) using heightmap {type}")
    
    # Verify heightmap type is valid
    valid_types = ["WORLD_SURFACE", "MOTION_BLOCKING", "MOTION_BLOCKING_NO_LEAVES", "OCEAN_FLOOR"]
    if type not in valid_types:
        raise ValueError(f"Invalid heightmap type: {type}. Valid types are: {', '.join(valid_types)}")
    
    try:
        # Get the heightmap data for a small area (1x1) around the requested position
        # We need to load a WorldSlice for this
        from gdpc.vector_tools import Rect
        
        # Create a 1x1 rectangle at the requested position
        rect = Rect((x, z), (1, 1))
        
        # Load the world slice
        world_slice = await anyio.to_thread.run_sync(lambda: editor.loadWorldSlice(rect))
        
        # Get the heightmap data (local coordinates within the slice will be 0,0)
        try:
            height = int(world_slice.heightmaps[type][0, 0])
            # Subtract 1 from the height because heightmaps contain the Y-level of the block above the terrain
            actual_height = height - 1
            
            return {
                "heightmap_type": type,
                "position": [x, z],
                "height": actual_height,
                "raw_height": height
            }
        except KeyError:
            raise ValueError(f"Heightmap type {type} not available")
        except IndexError:
            raise ValueError(f"Coordinates ({x},{z}) are outside the loaded world")
    except Exception as e:
        await ctx.error(f"Error getting height at ({x},{z}): {e}")
        raise ValueError(f"Failed to get height at ({x},{z}): {e}") from e


# Register tutorial tools
register_tutorial_tools(mcp)


# Optional: Define a main block to run the server directly (e.g., for simple deployments)
# def run_server_sync():
#      # This synchronous runner is simpler if you don't need async setup
#      mcp.run()

if __name__ == "__main__":
    # Run the server using the default stdio transport if the script is executed directly.
    # For SSE or other transports, use `fastmcp run ... --transport sse`
    logger.info("Running GDMC Bridge server via __main__ (stdio transport)...")
    mcp.run(transport="stdio")