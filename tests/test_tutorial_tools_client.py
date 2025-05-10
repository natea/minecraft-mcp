#!/usr/bin/env python3
"""
Test client for the GDMC MCP tutorial tools.
This demonstrates how to use the tutorial tools with proper context handling.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
import pytest

from fastmcp import Client

@pytest.mark.asyncio
async def test_tutorial_build_village_mock():
    """Run a test of the tutorial_build_village tool with a mock transport."""
    # For testing purposes, let's use a mock transport
    # This will allow us to test the client without actually connecting to a server
    from fastmcp.client.transports import ClientTransport
    
    # Create a mock transport for testing
    class MockTransport(ClientTransport):
        """A mock transport that doesn't actually connect to a server."""
        
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
            
        async def send_message(self, message):
            print(f"Mock transport would send: {message}")
            return {"result": "This is a mock response"}
        
        async def connect_session(self, **kwargs):
            """Implement the abstract method required by ClientTransport."""
            print("Mock transport connected")
            class AsyncContextManager:
                async def __aenter__(self_inner):
                    return self
                async def __aexit__(self_inner, exc_type, exc_val, exc_tb):
                    pass
            return AsyncContextManager()
    
    # Use the mock transport for testing
    transport = MockTransport()
    client = Client(transport)

    # Patch client to support async context manager
    async def aenter():
        return client

    async def aexit(exc_type, exc_val, exc_tb):
        return None

    client.__aenter__ = aenter
    client.__aexit__ = aexit

    # Use async context manager pattern
    async with client:
        # Test the tutorial_build_village tool
        result = await client.call_tool(
            "tutorial_build_village",
            {
                "position": [0, 65, 0],
                "size": 3
            }
        )
        
        # Verify we got a response
        assert isinstance(result, dict)
        assert "result" in result
        assert result["result"] == "This is a mock response"

if __name__ == "__main__":
    asyncio.run(test_tutorial_build_village_mock())