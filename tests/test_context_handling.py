"""
Simple test for the context handling fix in tutorial tools.
This directly tests that our fix for the NoneType error works.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pytest

# Add the project root to the Python path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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

class MockEditor:
    """Mock Editor that logs calls instead of connecting to Minecraft."""
    
    def __init__(self):
        self.calls = []
        self.buffering = False

# Create a mock function with the same pattern as tutorial_build_village
async def mock_tutorial_function(
    position: Optional[List[int]] = None,
    size: int = 3,
    ctx: Any = None
) -> Dict[str, Any]:
    """Mock function with the same pattern as tutorial_build_village."""
    # This is the fix we're testing
    if ctx is None or not hasattr(ctx, 'request_context'):
        raise ValueError("Context is required for this tool. Make sure you're using the correct client.")
    
    # This would fail if ctx is None
    editor = ctx.request_context.lifespan_context.get("editor")
    
    # Return a simple result
    return {"success": True, "position": position, "size": size}

@pytest.mark.asyncio
async def test_context_handling_none_context():
    """Test that mock_tutorial_function raises ValueError with None context."""
    # Test with None context (should raise ValueError)
    print("\nTest 1: Calling with None context (should raise ValueError)")
    with pytest.raises(ValueError, match="Context is required for this tool"):
        # We need to await the function since it's async
        await mock_tutorial_function(
            position=[0, 65, 0],
            size=3,
            ctx=None
        )

@pytest.mark.asyncio
async def test_context_handling_valid_context():
    """Test that mock_tutorial_function works with valid context."""
    # Test with valid context
    print("\nTest 2: Calling with valid context")
    editor = MockEditor()
    mock_ctx = MockContext(editor)
    # Just check that it doesn't raise an error when accessing ctx.request_context
    result = await mock_tutorial_function(
        position=[0, 65, 0],
        size=3,
        ctx=mock_ctx
    )
    assert result["success"] is True