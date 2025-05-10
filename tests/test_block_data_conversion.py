"""
Test script for the BlockData.to_block() method in the GDMC MCP server.
This script directly tests our fix for the BlockData.to_block() method.
"""
import sys
import os
from pathlib import Path
import pytest

# Add the project root to the Python path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gdpc import Block
from src.gdmc_mcp.models import BlockData

def test_block_data_to_block():
    """Test the BlockData.to_block() method directly."""
    print("Testing BlockData.to_block() method...")
    
    # Test cases
    test_cases = [
        # Basic block
        {"id": "minecraft:stone"},
        
        # Block with states
        {"id": "minecraft:oak_stairs", "states": {"facing": "north", "half": "bottom"}},
        
        # Block with data
        {"id": "minecraft:chest", "data": '{"Items":[{"id":"minecraft:diamond","Count":64,"Slot":0}]}'}
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest case {i+1}: {test_case}")
        
        # Create a BlockData instance
        block_data = BlockData(**test_case)
        
        # Convert to a GDPC Block object
        block_obj = block_data.to_block()
        
        # Verify the conversion worked
        print(f"Successfully converted BlockData to Block: {block_obj}")
        print(f"Block ID: {block_obj.id}")
        print(f"Block states: {block_obj.states}")
        print(f"Block data: {block_obj.data}")
        
        # Verify it's a proper GDPC Block instance
        assert isinstance(block_obj, Block)
        
        # Verify properties match
        assert block_obj.id == test_case["id"]
        
        if "states" in test_case:
            assert block_obj.states == test_case["states"]
        else:
            assert block_obj.states == {} # Default states should be empty dict
            
        if "data" in test_case:
            assert block_obj.data == test_case["data"]
        else:
            assert block_obj.data is None # Default data should be None