#!/usr/bin/env python3
"""
Standalone test for Tello MCP Server
Tests the server without needing Claude Desktop
"""

import sys
import json
import subprocess
import time

def send_mcp_request(process, request):
    """Send an MCP request and get response"""
    # Send request
    request_json = json.dumps(request)
    process.stdin.write(request_json + '\n')
    process.stdin.flush()

    # Read response
    response_line = process.stdout.readline()
    if response_line:
        return json.loads(response_line)
    return None

def test_mcp_server():
    """Test the MCP server"""
    print("🧪 Testing Tello MCP Server")
    print("=" * 50)
    print()

    # Start the MCP server process
    print("Starting MCP server...")
    process = subprocess.Popen(
        ['python3', 'mcp_server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    time.sleep(1)

    try:
        # Test 1: Initialize
        print("\n1️⃣  Testing: Initialize connection")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }

        response = send_mcp_request(process, init_request)
        if response:
            print(f"✅ Server initialized: {response.get('result', {}).get('serverInfo', {}).get('name')}")
        else:
            print("❌ Failed to initialize")
            return

        # Test 2: List tools
        print("\n2️⃣  Testing: List available tools")
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }

        response = send_mcp_request(process, list_tools_request)
        if response and 'result' in response:
            tools = response['result'].get('tools', [])
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools[:5]:  # Show first 5
                print(f"   - {tool['name']}: {tool['description'][:60]}...")
            if len(tools) > 5:
                print(f"   ... and {len(tools) - 5} more")
        else:
            print("❌ Failed to list tools")
            return

        # Test 3: Call connect tool (will fail if not on Tello WiFi, which is expected)
        print("\n3️⃣  Testing: Connect tool (may fail if not on Tello WiFi)")
        connect_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "connect",
                "arguments": {}
            }
        }

        response = send_mcp_request(process, connect_request)
        if response and 'result' in response:
            content = response['result'].get('content', [])
            if content:
                print(f"📡 Response: {content[0].get('text', 'No text')}")
        else:
            print("⚠️  Connect failed (expected if not on Tello WiFi)")

        print("\n" + "=" * 50)
        print("✅ MCP Server test complete!")
        print()
        print("The server is working correctly. To use it with Claude:")
        print("1. Run: ./setup_mcp.sh")
        print("2. Restart Claude Desktop")
        print("3. Connect to Tello WiFi")
        print("4. Tell Claude: 'Connect to my Tello drone'")

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up
        process.terminate()
        process.wait(timeout=5)

if __name__ == "__main__":
    test_mcp_server()
