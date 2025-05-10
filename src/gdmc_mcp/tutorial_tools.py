# src/gdmc_mcp/tutorial_tools.py
"""
Tools for running GDPC tutorials and building example structures in Minecraft.
"""

import logging
import random
import asyncio
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import numpy as np
from gdpc import Editor, Block, Transform
from gdpc import geometry, vector_tools
from gdpc.exceptions import BuildAreaNotSetError
from gdpc.vector_tools import ivec3, Box, addY

from . import gdpc_utils
from fastmcp import FastMCP

logger = logging.getLogger(__name__)

def register_tutorial_tools(mcp: FastMCP) -> None:
    """
    Register tutorial tools with the FastMCP server.
    
    Args:
        mcp: The FastMCP server instance
    """
    @mcp.tool()
    async def tutorial_build_house(
        position: Optional[List[int]] = None,
        auto_position: bool = True,
        ctx: Any = None
    ) -> Dict[str, Any]:
        """Build a simple house following the GDPC tutorial pattern."""
        if ctx is None or not hasattr(ctx, 'request_context'):
            raise ValueError("Context is required for this tool. Make sure you're using the correct client.")
        editor = ctx.request_context.lifespan_context.get("editor")
        pos_tuple = tuple(position) if position else None
        return await run_house_tutorial(editor, pos_tuple, auto_position)
    
    @mcp.tool()
    async def tutorial_analyze_terrain(
        position: Optional[List[int]] = None,
        ctx: Any = None
    ) -> Dict[str, Any]:
        """Analyze terrain using GDPC's WorldSlice and heightmaps."""
        if ctx is None or not hasattr(ctx, 'request_context'):
            raise ValueError("Context is required for this tool. Make sure you're using the correct client.")
        editor = ctx.request_context.lifespan_context.get("editor")
        pos_tuple = tuple(position) if position else None
        return await run_terrain_analysis_tutorial(editor, pos_tuple)
    
    @mcp.tool()
    async def tutorial_vector_demo(
        position: Optional[List[int]] = None,
        ctx: Any = None
    ) -> Dict[str, Any]:
        """Demonstrate GDPC vector operations with visual examples."""
        if ctx is None or not hasattr(ctx, 'request_context'):
            raise ValueError("Context is required for this tool. Make sure you're using the correct client.")
        editor = ctx.request_context.lifespan_context.get("editor")
        pos_tuple = tuple(position) if position else None
        return await run_vector_operations_demo(editor, pos_tuple)
    
    @mcp.tool()
    async def tutorial_transformation_demo(
        position: Optional[List[int]] = None,
        ctx: Any = None
    ) -> Dict[str, Any]:
        """Demonstrate GDPC's transformation system with visual examples."""
        if ctx is None or not hasattr(ctx, 'request_context'):
            raise ValueError("Context is required for this tool. Make sure you're using the correct client.")
        editor = ctx.request_context.lifespan_context.get("editor")
        pos_tuple = tuple(position) if position else None
        return await run_transformation_tutorial(editor, pos_tuple)
    
    @mcp.tool()
    async def tutorial_build_village(
        position: Optional[List[int]] = None,
        size: int = 3,
        ctx: Any = None
    ) -> Dict[str, Any]:
        """Build a small example village."""
        if ctx is None or not hasattr(ctx, 'request_context'):
            raise ValueError("Context is required for this tool. Make sure you're using the correct client.")
        editor = ctx.request_context.lifespan_context.get("editor")
        pos_tuple = tuple(position) if position else None
        return await build_example_village(editor, pos_tuple, size)
    
    @mcp.tool()
    async def tutorial_build_tower(
        position: Optional[List[int]] = None,
        height: int = 12,
        ctx: Any = None
    ) -> Dict[str, Any]:
        """Build a tower with a cylindrical base and conical roof."""
        if ctx is None or not hasattr(ctx, 'request_context'):
            raise ValueError("Context is required for this tool. Make sure you're using the correct client.")
        editor = ctx.request_context.lifespan_context.get("editor")
        pos_tuple = tuple(position) if position else None
        return await build_example_tower(editor, pos_tuple, height)
    
    @mcp.tool()
    async def tutorial_terrain_report(
        position: Optional[List[int]] = None,
        radius: int = 25,
        ctx: Any = None
    ) -> Dict[str, Any]:
        """Generate a detailed terrain analysis report."""
        if ctx is None or not hasattr(ctx, 'request_context'):
            raise ValueError("Context is required for this tool. Make sure you're using the correct client.")
        editor = ctx.request_context.lifespan_context.get("editor")
        pos_tuple = tuple(position) if position else None
        return await generate_terrain_report(editor, pos_tuple, radius)

async def run_house_tutorial(
    editor: Editor,
    position: Optional[Tuple[int, int, int]] = None,
    auto_position: bool = True
) -> Dict[str, Any]:
    """
    Run the house building tutorial from the GDPC documentation.
    
    Args:
        editor: The GDPC Editor instance
        position: Optional position to place the house
        auto_position: Whether to automatically find a suitable position if none is provided
        
    Returns:
        Dictionary with information about the built house
    """
    if position is None and auto_position:
        # Find a suitable position for the house
        pos, avg_height = await asyncio.to_thread.run_sync(
            lambda: gdpc_utils.find_build_position(editor)
        )
        position = (pos.x, pos.y, pos.z)
        
    if position is None:
        # Use the build area corner as fallback
        try:
            build_area = await asyncio.to_thread.run_sync(lambda: editor.getBuildArea())
            position = (build_area.offset.x, build_area.offset.y + 3, build_area.offset.z)
        except BuildAreaNotSetError:
            # If no build area is set, use a default position
            position = (0, 80, 0)
    
    # Generate random house parameters as in the tutorial
    height = random.randint(3, 7)
    depth = random.randint(5, 10)
    width = random.randint(5, 9)
    
    # Define random floor and wall materials
    floor_materials = ["stone_bricks", "cobblestone", "polished_andesite"]
    wall_materials = [
        "oak_planks", 
        "spruce_planks", 
        "birch_planks", 
        "dark_oak_planks",
        "white_terracotta",
        "green_terracotta"
    ]
    
    floor_material = random.choice(floor_materials)
    wall_material = random.choice(wall_materials)
    
    logger.info(f"Building tutorial house at {position} with height={height}, depth={depth}, width={width}")
    
    # Build the house
    house_info = await asyncio.to_thread.run_sync(
        lambda: gdpc_utils.build_house(
            editor, 
            position,
            height=height,
            depth=depth,
            width=width,
            wall_material=wall_material,
            floor_material=floor_material
        )
    )
    
    # Add some metadata
    house_info["tutorial"] = True
    house_info["message"] = "House built successfully following the GDPC tutorial pattern"
    
    return house_info

async def run_terrain_analysis_tutorial(
    editor: Editor,
    position: Optional[Tuple[int, int, int]] = None
) -> Dict[str, Any]:
    """
    Run the terrain analysis tutorial using WorldSlice and heightmaps.
    
    Args:
        editor: The GDPC Editor instance
        position: Optional center position for analysis
        
    Returns:
        Dictionary with terrain analysis results
    """
    # Get build area
    try:
        build_area = await asyncio.to_thread.run_sync(lambda: editor.getBuildArea())
    except BuildAreaNotSetError:
        raise ValueError("Build area not set. Use /setbuildarea in-game.")
    
    build_rect = build_area.toRect()
    
    if position is not None:
        # Create a smaller rect around the specified position
        x, y, z = position
        sub_rect_size = min(50, build_rect.size.x, build_rect.size.y)  # Max 50x50 area
        sub_rect = vector_tools.Rect(
            (x - sub_rect_size // 2, z - sub_rect_size // 2),
            (sub_rect_size, sub_rect_size)
        )
    else:
        # Use the whole build area
        sub_rect = build_rect
    
    # Run terrain analysis
    logger.info(f"Analyzing terrain in area: {sub_rect}")
    
    analysis_results = await asyncio.to_thread.run_sync(
        lambda: gdpc_utils.analyze_terrain(editor, sub_rect)
    )
    
    # Add tutorial specific info
    analysis_results["tutorial"] = True
    analysis_results["message"] = (
        "Terrain analysis complete. This demonstrates how to use WorldSlice "
        "and heightmaps to analyze the Minecraft terrain."
    )
    
    return analysis_results

async def run_vector_operations_demo(
    editor: Editor,
    position: Optional[Tuple[int, int, int]] = None
) -> Dict[str, Any]:
    """
    Create a demonstration of vector operations using the GDPC vector_tools.
    
    Args:
        editor: The GDPC Editor instance
        position: Optional starting position for the demo
        
    Returns:
        Dictionary with information about the demo
    """
    if position is None:
        # Try to get a good position from the build area
        try:
            build_area = await asyncio.to_thread.run_sync(lambda: editor.getBuildArea())
            position = (
                build_area.offset.x + build_area.size.x // 2,
                build_area.offset.y + 5,
                build_area.offset.z + build_area.size.z // 2
            )
        except BuildAreaNotSetError:
            # Default position if no build area
            position = (0, 80, 0)
    
    start_pos = ivec3(*position)
    
    # Define base position and message
    result = {
        "tutorial": True,
        "position": list(position),
        "message": "Vector operations demo complete. This demonstrates various vector utilities provided by GDPC.",
        "operations": []
    }
    
    # Ensure editor is in buffering mode for better performance
    buffering_state = editor.buffering
    editor.buffering = True
    
    try:
        # Clear the space
        await asyncio.to_thread.run_sync(
            lambda: geometry.placeCuboid(
                editor,
                start_pos - ivec3(10, 0, 10),
                start_pos + ivec3(10, 15, 10),
                Block("air")
            )
        )
        
        # Create a platform
        await asyncio.to_thread.run_sync(
            lambda: geometry.placeCuboid(
                editor,
                start_pos - ivec3(10, 1, 10),
                start_pos + ivec3(10, -1, 10),
                Block("smooth_stone")
            )
        )
        
        # 1. Line drawing - demonstrate line3D
        line_end = start_pos + ivec3(8, 8, 8)
        await asyncio.to_thread.run_sync(
            lambda: geometry.placeLine(
                editor, 
                start_pos,
                line_end,
                Block("red_concrete")
            )
        )
        result["operations"].append({
            "name": "line3D",
            "description": "A 3D line between two points",
            "start": list(start_pos),
            "end": list(line_end)
        })
        
        # 2. Circle drawing - demonstrate circle
        circle_center = start_pos + ivec3(0, 0, 0)
        circle_radius = 5
        
        # Convert to 2D points
        circle_points = [(p.x, p.z) for p in vector_tools.circle((circle_center.x, circle_center.z), circle_radius)]
        
        # Place blocks
        for px, pz in circle_points:
            await asyncio.to_thread.run_sync(
                lambda px=px, pz=pz: editor.placeBlock(
                    (px, circle_center.y, pz),
                    Block("blue_concrete")
                )
            )
        
        result["operations"].append({
            "name": "circle",
            "description": "A circle with specified radius",
            "center": [circle_center.x, circle_center.y, circle_center.z],
            "radius": circle_radius
        })
        
        # 3. Rectangle - demonstrate Rect
        rect_corner1 = start_pos + ivec3(-8, 0, -8)
        rect_corner2 = start_pos + ivec3(-3, 0, -3)
        rect = vector_tools.Rect.between(
            (rect_corner1.x, rect_corner1.z),
            (rect_corner2.x, rect_corner2.z)
        )
        
        # Place blocks at rectangle outline
        for px, pz in rect.outline:
            await asyncio.to_thread.run_sync(
                lambda px=px, pz=pz: editor.placeBlock(
                    (px, rect_corner1.y, pz),
                    Block("green_concrete")
                )
            )
        
        result["operations"].append({
            "name": "Rect",
            "description": "A rectangle outline defined by two corners",
            "corner1": [rect_corner1.x, rect_corner1.y, rect_corner1.z],
            "corner2": [rect_corner2.x, rect_corner2.y, rect_corner2.z]
        })
        
        # 4. Box - demonstrate Box
        box_corner1 = start_pos + ivec3(3, 1, -8)
        box_corner2 = start_pos + ivec3(8, 6, -3)
        
        await asyncio.to_thread.run_sync(
            lambda: geometry.placeCuboidWireframe(
                editor,
                box_corner1,
                box_corner2,
                Block("purple_concrete")
            )
        )
        
        result["operations"].append({
            "name": "Box",
            "description": "A 3D box wireframe defined by two corners",
            "corner1": list(box_corner1),
            "corner2": list(box_corner2)
        })
        
        # 5. Vector rotation - demonstrate rotate2D
        rotation_center = start_pos + ivec3(0, 0, 0)
        rotation_radius = 8
        rotation_height = 0
        
        # Place blocks at different rotations
        for angle in range(0, 360, 45):
            # Convert angle to radians
            rad_angle = angle * 3.14159 / 180
            
            # Calculate rotated position
            rot_x = rotation_center.x + int(rotation_radius * np.cos(rad_angle))
            rot_z = rotation_center.z + int(rotation_radius * np.sin(rad_angle))
            
            # Place a small column
            for y in range(3):
                await asyncio.to_thread.run_sync(
                    lambda rot_x=rot_x, y=y, rot_z=rot_z: editor.placeBlock(
                        (rot_x, rotation_center.y + y, rot_z),
                        Block("yellow_concrete")
                    )
                )
        
        result["operations"].append({
            "name": "rotate2D",
            "description": "Points arranged in a circle to demonstrate rotation",
            "center": list(rotation_center),
            "radius": rotation_radius
        })
        
        # Flush the buffer
        await asyncio.to_thread.run_sync(lambda: editor.flushBuffer())
        
    finally:
        # Restore buffering state
        editor.buffering = buffering_state
    
    return result

async def run_transformation_tutorial(
    editor: Editor,
    position: Optional[Tuple[int, int, int]] = None
) -> Dict[str, Any]:
    """
    Create a demonstration of GDPC's transformation system.
    
    Args:
        editor: The GDPC Editor instance
        position: Optional starting position for the demo
        
    Returns:
        Dictionary with information about the demo
    """
    if position is None:
        # Try to get a good position from the build area
        try:
            build_area = await asyncio.to_thread.run_sync(lambda: editor.getBuildArea())
            position = (
                build_area.offset.x + 10,
                build_area.offset.y + 5,
                build_area.offset.z + 10
            )
        except BuildAreaNotSetError:
            # Default position if no build area
            position = (0, 80, 0)
    
    start_pos = ivec3(*position)
    
    # Result structure
    result = {
        "tutorial": True,
        "position": list(position),
        "message": "Transformation demo complete. This demonstrates GDPC's transformation system.",
        "transformations": []
    }
    
    # Ensure editor is in buffering mode for better performance
    buffering_state = editor.buffering
    multithreading_state = editor.multithreading
    editor.buffering = True
    editor.multithreading = False
    
    try:
        # Clear the space for our demonstration
        await asyncio.to_thread.run_sync(
            lambda: geometry.placeCuboid(
                editor,
                start_pos - ivec3(15, 0, 15),
                start_pos + ivec3(40, 15, 40),
                Block("air")
            )
        )
        
        # Create a platform
        await asyncio.to_thread.run_sync(
            lambda: geometry.placeCuboid(
                editor,
                start_pos - ivec3(15, 1, 15),
                start_pos + ivec3(40, -1, 40),
                Block("smooth_stone")
            )
        )
        
        # Function to build a simple L-shaped structure
        def build_l_shape(local_editor):
            # Build an L-shaped structure
            # Base
            geometry.placeCuboid(
                local_editor, 
                (0, 0, 0), 
                (4, 0, 4), 
                Block("stone_bricks")
            )
            
            # Vertical parts - one arm of the L
            geometry.placeCuboid(
                local_editor,
                (0, 1, 0),
                (0, 3, 4),
                Block("oak_planks")
            )
            
            # Another arm of the L
            geometry.placeCuboid(
                local_editor,
                (0, 1, 0),
                (4, 3, 0),
                Block("oak_planks")
            )
            
            # Add stairs to show orientation
            local_editor.placeBlock(
                (2, 1, 2),
                Block("oak_stairs", {"facing": "north"})
            )
            
            # Add a banner to mark the structure
            local_editor.placeBlock(
                (0, 4, 0),
                Block("red_banner")
            )
        
        # 1. Original structure with no transformation
        with editor.pushTransform(Transform(start_pos)):
            await asyncio.to_thread.run_sync(lambda: build_l_shape(editor))
        
        result["transformations"].append({
            "name": "original",
            "description": "Original L-shaped structure with no transformation",
            "position": list(start_pos)
        })
        
        # 2. Translated structure
        translation_pos = start_pos + ivec3(15, 0, 0)
        with editor.pushTransform(Transform(translation_pos)):
            await asyncio.to_thread.run_sync(lambda: build_l_shape(editor))
        
        result["transformations"].append({
            "name": "translation",
            "description": "Structure translated to a new position",
            "position": list(translation_pos)
        })
        
        # 3. Rotated structure (90 degrees)
        rotation_pos = start_pos + ivec3(0, 0, 15)
        with editor.pushTransform(Transform(rotation_pos, rotation=1)):
            await asyncio.to_thread.run_sync(lambda: build_l_shape(editor))
        
        result["transformations"].append({
            "name": "rotation_90",
            "description": "Structure rotated 90 degrees",
            "position": list(rotation_pos),
            "rotation": 1
        })
        
        # 4. Rotated structure (180 degrees)
        rotation2_pos = start_pos + ivec3(15, 0, 15)
        with editor.pushTransform(Transform(rotation2_pos, rotation=2)):
            await asyncio.to_thread.run_sync(lambda: build_l_shape(editor))
        
        result["transformations"].append({
            "name": "rotation_180",
            "description": "Structure rotated 180 degrees",
            "position": list(rotation2_pos),
            "rotation": 2
        })
        
        # 5. Flipped structure (X-axis)
        flip_pos = start_pos + ivec3(30, 0, 0)
        with editor.pushTransform(Transform(flip_pos, flip=(True, False, False))):
            await asyncio.to_thread.run_sync(lambda: build_l_shape(editor))
        
        result["transformations"].append({
            "name": "flip_x",
            "description": "Structure flipped along the X-axis",
            "position": list(flip_pos),
            "flip": [True, False, False]
        })
        
        # 6. Combined transformation (translate, rotate, flip)
        combined_pos = start_pos + ivec3(30, 0, 15)
        with editor.pushTransform(Transform(combined_pos, rotation=3, flip=(False, False, True))):
            await asyncio.to_thread.run_sync(lambda: build_l_shape(editor))
        
        result["transformations"].append({
            "name": "combined",
            "description": "Structure with combined translation, rotation, and flip",
            "position": list(combined_pos),
            "rotation": 3,
            "flip": [False, False, True]
        })
        
        # Flush buffer to ensure all changes are applied
        await asyncio.to_thread.run_sync(lambda: editor.flushBuffer())
        
    finally:
        # Restore editor states
        editor.buffering = buffering_state
        editor.multithreading = multithreading_state
    
    return result

async def build_example_village(
    editor: Editor,
    position: Optional[Tuple[int, int, int]] = None,
    num_houses: int = 5,
    radius: int = 30
) -> Dict[str, Any]:
    """
    Build an example village using the GDPC framework.
    
    Args:
        editor: The GDPC Editor instance
        position: Optional center position for the village
        num_houses: Number of houses to generate
        radius: Radius of the village area
        
    Returns:
        Dictionary with information about the village
    """
    if position is None:
        # Find a suitable position
        pos, avg_height = await asyncio.to_thread.run_sync(
            lambda: gdpc_utils.find_build_position(editor)
        )
        position = (pos.x, pos.y, pos.z)
    
    logger.info(f"Building example village at {position} with {num_houses} houses")
    
    # Generate the village
    village_info = await asyncio.to_thread.run_sync(
        lambda: gdpc_utils.generate_village(
            editor,
            position,
            num_houses=num_houses,
            radius=radius
        )
    )
    
    return village_info

async def build_example_tower(
    editor: Editor,
    position: Optional[Tuple[int, int, int]] = None,
    height: Optional[int] = None,
    radius: Optional[int] = None,
    material: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build an example tower using the GDPC framework.
    
    Args:
        editor: The GDPC Editor instance
        position: Optional position for the tower
        height: Optional tower height
        radius: Optional tower radius
        material: Optional tower material
        
    Returns:
        Dictionary with information about the tower
    """
    if position is None:
        # Find a suitable position
        pos, avg_height = await asyncio.to_thread.run_sync(
            lambda: gdpc_utils.find_build_position(editor)
        )
        position = (pos.x, pos.y, pos.z)
    
    # Set default parameters if not provided
    if height is None:
        height = random.randint(8, 16)
    
    if radius is None:
        radius = random.randint(3, 5)
    
    if material is None:
        materials = ["stone_bricks", "deepslate_bricks", "polished_blackstone_bricks"]
        material = random.choice(materials)
    
    logger.info(f"Building example tower at {position} with height={height}, radius={radius}")
    
    # Build the tower
    tower_info = await asyncio.to_thread.run_sync(
        lambda: gdpc_utils.build_tower(
            editor,
            position,
            height=height,
            radius=radius,
            material=material
        )
    )
    
    return tower_info

async def generate_terrain_report(
    editor: Editor,
    position: Optional[Tuple[int, int, int]] = None,
    radius: int = 50
) -> Dict[str, Any]:
    """
    Generate a detailed terrain analysis report for an area.
    
    Args:
        editor: The GDPC Editor instance
        position: Optional center position for analysis
        radius: Radius of the area to analyze
        
    Returns:
        Dictionary with terrain analysis report
    """
    # Get build area
    try:
        build_area = await asyncio.to_thread.run_sync(lambda: editor.getBuildArea())
    except BuildAreaNotSetError:
        raise ValueError("Build area not set. Use /setbuildarea in-game.")
    
    # Set the center position
    if position is None:
        center_x = build_area.offset.x + build_area.size.x // 2
        center_z = build_area.offset.z + build_area.size.z // 2
        
        # Load world slice to get height
        editor.loadWorldSlice(build_area.toRect(), cache=True)
        heightmap = editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
        local_x = center_x - build_area.offset.x
        local_z = center_z - build_area.offset.z
        
        # Ensure coordinates are within bounds
        local_x = max(0, min(local_x, heightmap.shape[0] - 1))
        local_z = max(0, min(local_z, heightmap.shape[1] - 1))
        
        center_y = heightmap[local_x, local_z] - 1
        position = (center_x, center_y, center_z)
    
    # Create a rect for analysis
    x, y, z = position
    rect_size = min(radius * 2, build_area.size.x, build_area.size.z)
    
    analysis_rect = vector_tools.Rect(
        (x - rect_size // 2, z - rect_size // 2),
        (rect_size, rect_size)
    )
    
    # Ensure the rect is within the build area
    if (analysis_rect.offset.x < build_area.offset.x or
        analysis_rect.offset.y < build_area.offset.z or
        analysis_rect.offset.x + analysis_rect.size.x > build_area.offset.x + build_area.size.x or
        analysis_rect.offset.y + analysis_rect.size.y > build_area.offset.z + build_area.size.z):
        
        # Adjust rect to fit within build area
        analysis_rect = vector_tools.Rect(
            (
                max(build_area.offset.x, analysis_rect.offset.x),
                max(build_area.offset.z, analysis_rect.offset.y)
            ),
            (
                min(
                    build_area.offset.x + build_area.size.x - analysis_rect.offset.x,
                    analysis_rect.size.x
                ),
                min(
                    build_area.offset.z + build_area.size.z - analysis_rect.offset.y,
                    analysis_rect.size.y
                )
            )
        )
    
    # Run terrain analysis
    logger.info(f"Generating terrain report for area: {analysis_rect}")
    
    analysis_results = await asyncio.to_thread.run_sync(
        lambda: gdpc_utils.analyze_terrain(editor, analysis_rect)
    )
    
    return analysis_results