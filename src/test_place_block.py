#!/usr/bin/env python3
"""
Test script for the place_block tool in the GDMC MCP server.
This script directly tests our fix for the BlockData.to_block() method.
"""
import sys
import os
from pathlib import Path

# Add the project root to the Python path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gdpc import Block
from src.gdmc_mcp.models import BlockData

def main():
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
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest case {i+1}: {test_case}")
        
        # Create a BlockData instance
        block_data = BlockData(**test_case)
        
        try:
            # Convert to a GDPC Block object
            block_obj = block_data.to_block()
            
            # Verify the conversion worked
            print(f"Successfully converted BlockData to Block: {block_obj}")
            print(f"Block ID: {block_obj.id}")
            print(f"Block states: {block_obj.states}")
            print(f"Block data: {block_obj.data}")
            
            # Verify it's a proper GDPC Block instance
            if isinstance(block_obj, Block):
                print("✅ Test passed: BlockData.to_block() returns a valid GDPC Block instance")
                
                # Verify properties match
                if block_obj.id != test_case["id"]:
                    print(f"❌ ID mismatch: Expected {test_case['id']}, got {block_obj.id}")
                    all_passed = False
                
                if "states" in test_case and block_obj.states != test_case["states"]:
                    print(f"❌ States mismatch: Expected {test_case['states']}, got {block_obj.states}")
                    all_passed = False
                    
                if "data" in test_case and block_obj.data != test_case["data"]:
                    print(f"❌ Data mismatch: Expected {test_case['data']}, got {block_obj.data}")
                    all_passed = False
            else:
                print(f"❌ Test failed: Expected Block instance, got {type(block_obj)}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            all_passed = False
    
    if all_passed:
        print("\n✅ All tests passed! The BlockData.to_block() method is working correctly.")
    else:
        print("\n❌ Some tests failed. The BlockData.to_block() method needs further fixes.")
        
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)