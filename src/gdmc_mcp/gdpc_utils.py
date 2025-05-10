# src/gdmc_mcp/gdpc_utils.py
"""
Utility functions for interacting with GDPC and building structures in Minecraft.
"""

import logging
import math
import random
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import numpy as np
from gdpc import Editor, Block, Transform
from gdpc import geometry, minecraft_tools, editor_tools
from gdpc.exceptions import BuildAreaNotSetError
from gdpc.vector_tools import ivec2, ivec3, Rect, Box, addY, line2D, DIRECTIONS, rotate2D

logger = logging.getLogger(__name__)

# =============== TERRAIN ANALYSIS FUNCTIONS ===============

def find_build_position(editor: Editor) -> Tuple[ivec3, float]:
    """
    Find a suitable position to build in the current build area.
    
    Args:
        editor: The GDPC Editor instance
        
    Returns:
        Tuple containing:
        - Position vector (ivec3)
        - Average height at that position
    """
    # Get the build area
    try:
        build_area = editor.getBuildArea()
    except BuildAreaNotSetError:
        raise ValueError("Build area not set. Use /setbuildarea in-game.")
    
    build_rect = build_area.toRect()
    
    # Load the world slice for heightmap access
    editor.loadWorldSlice(build_rect, cache=True)
    heightmap = editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
    
    # Find the flattest area
    best_pos = None
    best_flatness = float('inf')  # Lower is better
    best_avg_height = 0
    
    # Sample size for checking flatness
    sample_size = 7  # Adjust based on your needs
    
    # Step size for scanning (to avoid checking every position)
    step = 3
    
    # Only check positions that leave enough room for a structure
    margin = sample_size + 2
    
    # Scan the heightmap
    x_range = range(margin, heightmap.shape[0] - margin, step)
    z_range = range(margin, heightmap.shape[1] - margin, step)
    
    for x in x_range:
        for z in z_range:
            # Get sample area heights
            heights = heightmap[x-sample_size//2:x+sample_size//2+1, 
                              z-sample_size//2:z+sample_size//2+1]
            
            # Calculate variance (lower variance = flatter terrain)
            flatness = np.var(heights)
            avg_height = np.mean(heights)
            
            # Skip if too close to water level or too high
            if 60 <= avg_height <= 120:
                if best_pos is None or flatness < best_flatness:
                    best_flatness = flatness
                    best_pos = (x, z)
                    best_avg_height = avg_height
    
    if best_pos is None:
        # Fallback if no suitable spot found
        center_x = heightmap.shape[0] // 2
        center_z = heightmap.shape[1] // 2
        best_pos = (center_x, center_z)
        best_avg_height = heightmap[center_x, center_z]
        
    # Convert to global coordinates
    global_x = best_pos[0] + build_rect.offset.x
    global_z = best_pos[1] + build_rect.offset.y  # Rect uses y for z
    global_y = int(best_avg_height)
    
    return ivec3(global_x, global_y, global_z), best_avg_height

def analyze_terrain(editor: Editor, rect: Rect) -> Dict[str, Any]:
    """
    Analyze the terrain in the specified rectangle.
    
    Args:
        editor: The GDPC Editor instance
        rect: Rectangle area to analyze
        
    Returns:
        Dictionary with analysis results
    """
    # Load the world slice
    editor.loadWorldSlice(rect, cache=True)
    world_slice = editor.worldSlice
    
    # Get heightmaps
    heightmap = world_slice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
    surface_heightmap = world_slice.heightmaps["WORLD_SURFACE"]
    
    # Calculate height statistics
    min_height = int(np.min(heightmap))
    max_height = int(np.max(heightmap))
    avg_height = float(np.mean(heightmap))
    std_dev = float(np.std(heightmap))
    
    # Detect water areas
    water_blocks = []
    trees = []
    biome_counts = {}
    
    # Sample some positions to detect features (to avoid checking every block)
    step = 3
    height_range = 20  # Check this many blocks up and down from heightmap
    
    for x in range(0, rect.size.x, step):
        for z in range(0, rect.size.y, step):  # Rect uses y for z
            # Get the height at this position
            height = heightmap[x, z]
            
            # Get the biome
            global_x = x + rect.offset.x
            global_z = z + rect.offset.y
            
            # Check for water
            for y in range(max(int(height) - 10, 58), int(height) + 2):
                block = world_slice.getBlock((x, y, z))
                if block and "water" in block.id:
                    water_blocks.append((global_x, y, global_z))
                    break
                    
            # Check for trees (simplified)
            for y in range(int(height), int(height) + height_range):
                block = world_slice.getBlock((x, y, z))
                if block and "log" in block.id:
                    trees.append((global_x, y, global_z))
                    break
            
            # Get biome
            biome = world_slice.getBiome((x, height, z))
            if biome:
                biome = biome.split(":")[-1]  # Extract name from namespace
                biome_counts[biome] = biome_counts.get(biome, 0) + 1
    
    # Sort biomes by frequency
    sorted_biomes = sorted(biome_counts.items(), key=lambda x: x[1], reverse=True)
    primary_biome = sorted_biomes[0][0] if sorted_biomes else "unknown"
    
    # Analyze terrain flatness (higher value = more varied)
    flatness_score = float(std_dev)
    if flatness_score < 3:
        terrain_type = "very flat"
    elif flatness_score < 7:
        terrain_type = "flat"
    elif flatness_score < 15:
        terrain_type = "hilly"
    else:
        terrain_type = "mountainous"
    
    # Determine water coverage
    water_coverage = len(water_blocks) / (rect.size.x * rect.size.y / (step * step))
    water_description = "none"
    if water_coverage > 0.5:
        water_description = "extensive"
    elif water_coverage > 0.2:
        water_description = "moderate"
    elif water_coverage > 0.05:
        water_description = "light"
    
    # Determine forestation level
    tree_density = len(trees) / (rect.size.x * rect.size.y / (step * step))
    tree_description = "barren"
    if tree_density > 0.2:
        tree_description = "heavily forested"
    elif tree_density > 0.1:
        tree_description = "forested"
    elif tree_density > 0.02:
        tree_description = "lightly forested"
    
    # Create terrain visualization (mark build area bounds)
    height_center = int((max_height + min_height) / 2)
    editor_tools.placeCuboidWireframe(
        editor, 
        (rect.offset.x, height_center, rect.offset.y),
        (rect.offset.x + rect.size.x - 1, height_center, rect.offset.y + rect.size.y - 1),
        Block("red_wool")
    )
    
    # Return analysis results
    return {
        "dimensions": {
            "width": rect.size.x,
            "depth": rect.size.y
        },
        "height_statistics": {
            "min_height": min_height,
            "max_height": max_height,
            "average_height": round(avg_height, 2),
            "standard_deviation": round(std_dev, 2)
        },
        "terrain_type": terrain_type,
        "primary_biome": primary_biome,
        "biome_distribution": dict(sorted_biomes[:5]),  # Top 5 biomes
        "water": {
            "coverage": round(water_coverage * 100, 1),
            "description": water_description,
            "sample_count": len(water_blocks)
        },
        "vegetation": {
            "tree_density": round(tree_density * 100, 1),
            "description": tree_description,
            "sample_count": len(trees)
        },
        "build_recommendations": get_build_recommendations(
            terrain_type, primary_biome, water_description, tree_description,
            min_height, max_height
        )
    }

def get_build_recommendations(
    terrain_type: str, 
    primary_biome: str, 
    water_description: str, 
    tree_description: str,
    min_height: int,
    max_height: int
) -> List[Dict[str, str]]:
    """Generate building recommendations based on terrain analysis."""
    recommendations = []
    
    # Basic recommendations based on terrain type
    if terrain_type == "very flat" or terrain_type == "flat":
        recommendations.append({
            "type": "settlement",
            "description": "Flat terrain is ideal for village-style settlements with connected buildings."
        })
    
    if terrain_type == "hilly" or terrain_type == "mountainous":
        recommendations.append({
            "type": "multi-level",
            "description": "Consider multi-level structures or buildings connected by bridges and walkways."
        })
        
        recommendations.append({
            "type": "towers",
            "description": "Towers and vertical structures work well in varied terrain."
        })
    
    # Biome-specific recommendations
    if "desert" in primary_biome:
        recommendations.append({
            "type": "palette",
            "description": "Use sandstone, terracotta, and smooth stone for authentic desert builds."
        })
    elif "forest" in primary_biome or "taiga" in primary_biome:
        recommendations.append({
            "type": "palette",
            "description": "Wood and stone materials blend well with the natural environment."
        })
    elif "mountain" in primary_biome:
        recommendations.append({
            "type": "style",
            "description": "Consider dwarf-inspired designs carved into mountainsides."
        })
    elif "plains" in primary_biome:
        recommendations.append({
            "type": "style",
            "description": "Traditional village-style structures work well in plains."
        })
    
    # Water-related recommendations
    if water_description in ["moderate", "extensive"]:
        recommendations.append({
            "type": "water",
            "description": "Incorporate waterways into your design or build structures over water."
        })
    
    # Tree-related recommendations
    if tree_description in ["forested", "heavily forested"]:
        recommendations.append({
            "type": "vegetation",
            "description": "Consider building treehouses or structures integrated with existing trees."
        })
    
    # Height-based recommendations
    if max_height - min_height > 20:
        recommendations.append({
            "type": "elevation",
            "description": "Use the natural elevation changes to create dramatic multi-level structures."
        })
    
    return recommendations

# =============== BUILDING FUNCTIONS ===============

def build_house(
    editor: Editor, 
    position: Union[ivec3, Tuple[int, int, int]],
    height: int = 5,
    depth: int = 8,
    width: int = 5,
    wall_material: str = "oak_planks",
    floor_material: str = "stone_bricks"
) -> Dict[str, Any]:
    """
    Build a house at the specified position.
    
    Args:
        editor: The GDPC Editor instance
        position: Starting (corner) position for the house
        height: Height of the house
        depth: Depth of the house
        width: Width of the house (must be odd for door placement)
        wall_material: Material for walls
        floor_material: Material for the floor
        
    Returns:
        Dictionary with information about the built house
    """
    # Convert position to ivec3 if it's a tuple
    pos = ivec3(*position) if isinstance(position, tuple) else position
    x, y, z = pos.x, pos.y, pos.z
    
    # Make sure width is odd for centered door
    if width % 2 == 0:
        width += 1
    
    # Create floor palette for more natural look
    floor_palette = [
        Block(floor_material),
        Block(floor_material),
        Block(floor_material),
        Block("cracked_stone_bricks") if "stone_bricks" in floor_material else Block(floor_material),
        Block("cobblestone") if "stone" in floor_material else Block(floor_material)
    ]
    
    wall_block = Block(wall_material)
    
    # Build main shape
    geometry.placeCuboidHollow(editor, (x, y, z), (x + width - 1, y + height - 1, z + depth - 1), wall_block)
    geometry.placeCuboid(editor, (x, y, z), (x + width - 1, y, z + depth - 1), floor_palette)
    
    # Foundation (for uneven terrain)
    foundation_depth = 5
    geometry.placeCuboid(editor, (x, y, z), (x + width - 1, y - foundation_depth, z + depth - 1), floor_palette)
    
    # Clear interior space
    interior_width = width - 2
    interior_depth = depth - 2
    geometry.placeCuboid(
        editor, 
        (x + 1, y + 1, z + 1), 
        (x + width - 2, y + height - 2, z + depth - 2), 
        Block("air")
    )
    
    # Add a door in the center of the front wall
    door_x = x + width // 2
    door_block = Block("oak_door", {"facing": "north", "hinge": "left"})
    editor.placeBlock((door_x, y + 1, z), door_block)
    
    # Clear space in front of the door
    geometry.placeCuboid(editor, (door_x - 1, y + 1, z - 1), (door_x + 1, y + 3, z - 1), Block("air"))
    
    # Add windows
    # Front windows (on either side of the door)
    if width >= 5:
        editor.placeBlock((x + 1, y + 2, z), Block("glass_pane", {"east": "true", "west": "true"}))
        editor.placeBlock((x + width - 2, y + 2, z), Block("glass_pane", {"east": "true", "west": "true"}))
    
    # Side windows
    for side_z in range(z + 2, z + depth - 2, 2):
        editor.placeBlock((x, y + 2, side_z), Block("glass_pane", {"north": "true", "south": "true"}))
        editor.placeBlock((x + width - 1, y + 2, side_z), Block("glass_pane", {"north": "true", "south": "true"}))
    
    # Back window
    back_x = x + width // 2
    editor.placeBlock((back_x, y + 2, z + depth - 1), Block("glass_pane", {"east": "true", "west": "true"}))
    
    # Build roof: pitched roof with stairs
    for dx in range(1, width // 2 + 2):
        if dx > width // 2:
            continue
            
        yy = y + height + 2 - dx
        
        # Build row of stairs blocks
        left_block = Block("oak_stairs", {"facing": "east"})
        right_block = Block("oak_stairs", {"facing": "west"})
        
        geometry.placeCuboid(editor, (x + width // 2 - dx, yy, z - 1), (x + width // 2 - dx, yy, z + depth), left_block)
        geometry.placeCuboid(editor, (x + width // 2 + dx, yy, z - 1), (x + width // 2 + dx, yy, z + depth), right_block)
        
        # Add upside-down accent blocks at the front and back
        left_block_top = Block("oak_stairs", {"facing": "west", "half": "top"})
        right_block_top = Block("oak_stairs", {"facing": "east", "half": "top"})
        
        for zz in [z - 1, z + depth]:
            editor.placeBlock((x + width // 2 - dx + 1, yy, zz), left_block_top)
            editor.placeBlock((x + width // 2 + dx - 1, yy, zz), right_block_top)
    
    # Build the top row of the roof
    roof_top_y = y + height + 1
    geometry.placeCuboid(
        editor, 
        (x + width // 2, roof_top_y, z - 1), 
        (x + width // 2, roof_top_y, z + depth), 
        Block("oak_planks")
    )
    
    # Add light inside
    light_y = y + height - 2
    editor.placeBlock((x + width // 2, light_y, z + depth // 2), Block("lantern"))
    
    # Add some interior decoration
    if width >= 5 and depth >= 6:
        # Bed
        bed_x = x + width - 3
        bed_z = z + depth - 2
        editor.placeBlock((bed_x, y + 1, bed_z), Block("red_bed", {"facing": "west", "part": "foot"}))
        editor.placeBlock((bed_x, y + 1, bed_z - 1), Block("red_bed", {"facing": "west", "part": "head"}))
        
        # Crafting table
        editor.placeBlock((x + 1, y + 1, z + depth - 2), Block("crafting_table"))
        
        # Small table with torch
        if depth >= 8:
            editor.placeBlock((x + width // 2, y + 1, z + 2), Block("oak_fence"))
            editor.placeBlock((x + width // 2, y + 2, z + 2), Block("torch"))
    
    # Return information about the house
    return {
        "type": "house",
        "position": [x, y, z],
        "dimensions": {
            "width": width,
            "height": height,
            "depth": depth
        },
        "materials": {
            "walls": wall_material,
            "floor": floor_material
        }
    }

def build_tower(
    editor: Editor, 
    position: Union[ivec3, Tuple[int, int, int]],
    height: int = 12,
    radius: int = 3,
    material: str = "stone_bricks"
) -> Dict[str, Any]:
    """
    Build a tower with a cylindrical base and conical roof.
    
    Args:
        editor: The GDPC Editor instance
        position: Center position for the tower base
        height: Height of the tower
        radius: Radius of the tower
        material: Material for the tower walls
        
    Returns:
        Dictionary with information about the built tower
    """
    # Convert position to ivec3 if it's a tuple
    pos = ivec3(*position) if isinstance(position, tuple) else position
    x, y, z = pos.x, pos.y, pos.z
    
    # Create material palette for more natural look
    wall_palette = [
        Block(material),
        Block(material),
        Block(material),
        Block("cracked_stone_bricks") if "stone_bricks" in material else Block(material),
        Block("mossy_stone_bricks") if "stone_bricks" in material else Block(material)
    ]
    
    # Determine roof material based on wall material
    roof_material = "dark_oak_planks"
    if "stone" in material:
        roof_material = "dark_prismarine"
    elif "brick" in material:
        roof_material = "dark_oak_planks"
    
    # Build the cylindrical base
    for y_level in range(height):
        for rx in range(-radius, radius + 1):
            for rz in range(-radius, radius + 1):
                # Distance from center
                distance = math.sqrt(rx * rx + rz * rz)
                
                # Place wall blocks in a circle
                if radius - 1 <= distance <= radius:
                    editor.placeBlock((x + rx, y + y_level, z + rz), random.choice(wall_palette))
                    
                # Clear interior
                elif distance < radius - 1:
                    editor.placeBlock((x + rx, y + y_level, z + rz), Block("air"))
    
    # Build conical roof
    roof_height = radius * 2
    for y_level in range(roof_height + 1):
        roof_radius = radius * (1 - y_level / roof_height)
        for rx in range(-radius - 1, radius + 2):
            for rz in range(-radius - 1, radius + 2):
                distance = math.sqrt(rx * rx + rz * rz)
                if distance <= roof_radius:
                    editor.placeBlock((x + rx, y + height + y_level, z + rz), Block(roof_material))
    
    # Add a door
    door_x, door_y, door_z = x, y, z - radius
    editor.placeBlock((door_x, y + 1, door_z), Block("oak_door", {"facing": "south", "hinge": "left"}))
    
    # Clear doorway
    editor.placeBlock((door_x, y + 1, door_z), Block("oak_door", {"facing": "south", "hinge": "left"}))
    editor.placeBlock((door_x, y + 2, door_z), Block("air"))
    
    # Add windows
    window_heights = [height // 3, 2 * height // 3]
    for window_y in window_heights:
        for direction in range(4):
            angle = direction * math.pi / 2
            window_x = x + int(radius * math.cos(angle))
            window_z = z + int(radius * math.sin(angle))
            
            # Skip the door position
            if window_x == door_x and window_z == door_z:
                continue
                
            editor.placeBlock((window_x, y + window_y, window_z), Block("glass"))
    
    # Add lighting
    editor.placeBlock((x, y + 1, z), Block("lantern"))
    editor.placeBlock((x, y + height - 2, z), Block("lantern"))
    
    # Add a flag on top
    editor.placeBlock((x, y + height + roof_height + 1, z), Block("oak_fence"))
    editor.placeBlock((x, y + height + roof_height + 2, z), Block("red_banner"))
    
    # Return information about the tower
    return {
        "type": "tower",
        "position": [x, y, z],
        "dimensions": {
            "height": height,
            "radius": radius,
            "roof_height": roof_height
        },
        "materials": {
            "walls": material,
            "roof": roof_material
        }
    }

def generate_village(
    editor: Editor,
    center_position: Union[ivec3, Tuple[int, int, int]],
    num_houses: int = 5,
    radius: int = 30
) -> Dict[str, Any]:
    """
    Generate a small village with houses, paths, and decorations.
    
    Args:
        editor: The GDPC Editor instance
        center_position: Center position for the village
        num_houses: Number of houses to generate
        radius: Radius of the village area
        
    Returns:
        Dictionary with information about the generated village
    """
    # Convert position to ivec3 if it's a tuple
    center = ivec3(*center_position) if isinstance(center_position, tuple) else center_position
    x, y, z = center.x, center.y, center.z
    
    # Load world slice for heightmap access
    build_area = editor.getBuildArea()
    build_rect = build_area.toRect()
    editor.loadWorldSlice(build_rect, cache=True)
    heightmap = editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
    
    # Create a list to store information about built structures
    structures = []
    
    # Generate a village center - a well or gathering area
    central_structure = {
        "type": "well",
        "position": [x, y, z]
    }
    
    # Build a well at the center
    build_well(editor, (x, y, z))
    structures.append(central_structure)
    
    # Define possible house materials
    house_materials = [
        "oak_planks",
        "spruce_planks",
        "birch_planks",
        "dark_oak_planks"
    ]
    
    # Generate houses around the center
    for i in range(num_houses):
        # Find a position for the house
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(radius * 0.3, radius * 0.9)
        
        # Calculate position
        house_x = x + int(distance * math.cos(angle))
        house_z = z + int(distance * math.sin(angle))
        
        # Get the height at this position
        local_x = house_x - build_rect.offset.x
        local_z = house_z - build_rect.offset.y
        
        # Skip if out of bounds
        if (local_x < 0 or local_x >= heightmap.shape[0] or 
            local_z < 0 or local_z >= heightmap.shape[1]):
            continue
            
        # Get height and adjust position
        house_y = heightmap[local_x, local_z] - 1  # Subtract 1 as heightmap returns height of block above
        
        # Randomize house parameters
        height = random.randint(3, 6)
        depth = random.randint(6, 9)
        width = random.randint(5, 7)
        wall_material = random.choice(house_materials)
        
        # Build the house
        house_info = build_house(
            editor, 
            (house_x, house_y, house_z),
            height=height,
            depth=depth,
            width=width,
            wall_material=wall_material
        )
        
        structures.append(house_info)
        
        # Add some decoration around the house
        decorate_area(editor, (house_x, house_y, house_z), width, depth)
    
    # Generate paths connecting the houses to the center
    for structure in structures[1:]:  # Skip the center
        start_pos = ivec3(x, y, z)
        end_pos = ivec3(*structure["position"])
        
        # Adjust Y values based on heightmap
        build_path(editor, start_pos, end_pos, build_rect, heightmap)
    
    # Return information about the village
    return {
        "type": "village",
        "center": [x, y, z],
        "radius": radius,
        "structures": structures
    }

def build_well(editor: Editor, position: Union[ivec3, Tuple[int, int, int]]) -> None:
    """
    Build a well at the specified position.
    
    Args:
        editor: The GDPC Editor instance
        position: Center position for the well
    """
    # Convert position to ivec3 if it's a tuple
    pos = ivec3(*position) if isinstance(position, tuple) else position
    x, y, z = pos.x, pos.y, pos.z
    
    # Build well base
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            # Skip corners for a more rounded shape
            if abs(dx) == 2 and abs(dz) == 2:
                continue
                
            editor.placeBlock((x + dx, y, z + dz), Block("stone_bricks"))
    
    # Build well walls
    for dx, dz in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        editor.placeBlock((x + dx * 2, y + 1, z + dz * 2), Block("cobblestone_wall"))
        editor.placeBlock((x + dx * 2, y + 2, z + dz * 2), Block("cobblestone_wall"))
    
    # Add fence tops
    for dx in [-2, 0, 2]:
        for dz in [-2, 0, 2]:
            # Skip center and corners
            if (dx == 0 and dz == 0) or (abs(dx) == 2 and abs(dz) == 2):
                continue
                
            editor.placeBlock((x + dx, y + 1, z + dz), Block("oak_fence"))
    
    # Add roof structure
    roof_y = y + 3
    for dx in range(-1, 2):
        for dz in range(-1, 2):
            editor.placeBlock((x + dx, roof_y, z + dz), Block("oak_slab"))
    
    # Add water
    for dx in range(-1, 2):
        for dz in range(-1, 2):
            # Central water column goes deeper
            depth = 3 if dx == 0 and dz == 0 else 1
            for dy in range(1, depth + 1):
                editor.placeBlock((x + dx, y - dy, z + dz), Block("water"))
                
    # Add decorative slabs around the well
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            # Skip the well itself and create a circular pattern
            dist = math.sqrt(dx * dx + dz * dz)
            if 2.5 <= dist <= 3.5:
                editor.placeBlock((x + dx, y, z + dz), Block("stone_slab"))

def decorate_area(
    editor: Editor, 
    position: Union[ivec3, Tuple[int, int, int]],
    width: int,
    depth: int
) -> None:
    """
    Add decorations around a house or structure.
    
    Args:
        editor: The GDPC Editor instance
        position: Starting position of the structure
        width: Width of the structure
        depth: Depth of the structure
    """
    # Convert position to ivec3 if it's a tuple
    pos = ivec3(*position) if isinstance(position, tuple) else position
    x, y, z = pos.x, pos.y, pos.z
    
    # Define decoration items
    decorations = [
        ("oak_fence", "lantern"),
        ("spruce_fence", "flower_pot"),
        ("barrel", None),
        ("campfire", None),
        ("composter", None)
    ]
    
    # Define possible flowers
    flowers = [
        "poppy", "dandelion", "blue_orchid", "allium", 
        "azure_bluet", "red_tulip", "orange_tulip", "white_tulip"
    ]
    
    # Add decorations around the house
    num_decorations = random.randint(2, 5)
    
    # Select positions around the house
    decoration_positions = []
    
    # Front area
    front_x = x + width // 2
    front_z = z - 2
    decoration_positions.append((front_x, y, front_z))
    
    # Side areas
    for side_z in range(z + 2, z + depth - 2, 3):
        decoration_positions.append((x - 2, y, side_z))
        decoration_positions.append((x + width + 1, y, side_z))
    
    # Back area
    back_x = x + width // 2
    back_z = z + depth + 1
    decoration_positions.append((back_x, y, back_z))
    
    # Randomly select positions and add decorations
    selected_positions = random.sample(decoration_positions, min(num_decorations, len(decoration_positions)))
    
    for pos in selected_positions:
        # Choose a random decoration
        base, top = random.choice(decorations)
        
        # Place the base decoration
        editor.placeBlock(pos, Block(base))
        
        # Place the top decoration if any
        if top:
            if top == "flower_pot":
                flower = random.choice(flowers)
                # Use string formatting instead of f-string to avoid escaping issues
                pot_block = Block("flower_pot", data='{Contents:{id:"%s"}}' % flower)
                editor.placeBlock((pos[0], pos[1] + 1, pos[2]), pot_block)
            else:
                editor.placeBlock((pos[0], pos[1] + 1, pos[2]), Block(top))
        
    # Add some random flowers or grass around
    for _ in range(random.randint(5, 10)):
        dx = random.randint(-5, width + 5)
        dz = random.randint(-5, depth + 5)
        
        # Skip positions too close to the house
        if -1 <= dx <= width and -1 <= dz <= depth:
            continue
            
        # Place a flower or grass
        if random.random() < 0.7:
            editor.placeBlock((x + dx, y + 1, z + dz), Block(random.choice(flowers)))
        else:
            editor.placeBlock((x + dx, y + 1, z + dz), Block("grass"))

def build_path(
    editor: Editor, 
    start: ivec3, 
    end: ivec3,
    build_rect: Rect,
    heightmap: np.ndarray
) -> None:
    """
    Build a path between two points, following the terrain.
    
    Args:
        editor: The GDPC Editor instance
        start: Starting position
        end: Ending position
        build_rect: Build area rectangle
        heightmap: Terrain heightmap
    """
    # Generate the path points in 2D
    path_points = line2D((start.x, start.z), (end.x, end.z))
    
    # Path material palette
    path_palette = [
        Block("grass_path"),
        Block("grass_path"),
        Block("grass_path"),
        Block("coarse_dirt"),
        Block("gravel")
    ]
    
    # Build the path
    for point in path_points:
        # Convert to local coordinates
        local_x = point[0] - build_rect.offset.x
        local_z = point[1] - build_rect.offset.y
        
        # Check if point is within build area
        if (0 <= local_x < heightmap.shape[0] and 
            0 <= local_z < heightmap.shape[1]):
            
            # Get height at this position
            height = heightmap[local_x, local_z] - 1
            
            # Place path block
            editor.placeBlock((point[0], height, point[1]), random.choice(path_palette))
            
            # Add occasional lantern for night lighting
            if random.random() < 0.05:
                editor.placeBlock((point[0], height + 1, point[1]), Block("lantern"))