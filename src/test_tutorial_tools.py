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

from fastmcp import Client

async def main():
    """Run a test of the tutorial_build_village tool."""
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
            return self
    
    # Use the mock transport for testing
    transport = MockTransport()
    client = Client(transport)
    
    # Use async context manager pattern
    async with client:
        print("Connected to GDMC MCP server")
        
        try:
            # Test the tutorial_build_village tool
            print("\n--- Testing tutorial_build_village tool ---")
            result = await client.call_tool(
                "tutorial_build_village",
                {
                    "position": [0, 65, 0],
                    "size": 3
                }
            )
            
            print(f"Result: {json.dumps(result, indent=2)}")
            print("\nTest completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            
        # The context manager will handle disconnection automatically
        print("Disconnected from GDMC MCP server")


if __name__ == "__main__":
    asyncio.run(main())