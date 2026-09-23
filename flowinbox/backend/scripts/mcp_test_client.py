#!/usr/bin/env python3
"""
FlowInbox AI — MCP Server Verification Client
Tests authentication, tool discovery, and tool execution against /mcp endpoint.
"""
import sys
import json
import urllib.request
import urllib.error

MCP_URL = "http://localhost:8000/mcp"


def main():
    print("=== FlowInbox AI MCP Server Test Client ===")
    print(f"Target Endpoint: {MCP_URL}")

    # 1. Request test token or use provided token
    token = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not token:
        print("\n[Step 1] Requesting new test API token from backend...")
        try:
            req = urllib.request.Request(
                "http://localhost:8000/api/v1/api-tokens",
                data=json.dumps({"name": "MCP Verification Script Token"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                token = res_data.get("token")
                print(f"✓ Created test API token: {token[:12]}...{token[-6:]}")
        except Exception as err:
            print(f"⚠ Could not generate token via API: {err}")
            token = "fl_token_test_verification_key_12345"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 2. Test Tool Listing (GET /mcp)
    print("\n[Step 2] Testing Tool Discovery (GET /mcp)...")
    try:
        req = urllib.request.Request(MCP_URL, headers=headers, method="GET")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"✓ MCP Server Response Status: {data.get('status')}")
            print(f"✓ Authenticated User ID: {data.get('authenticated_user_id')}")
            tools = data.get("tools", [])
            print(f"✓ Discovered {len(tools)} Registered Tools:")
            for t in tools:
                print(f"   - {t['name']}: {t['description']}")
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.read().decode('utf-8')}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        sys.exit(1)

    # 3. Test Tool Execution (POST /mcp/tools/call)
    print("\n[Step 3] Testing Tool Execution ('list_pending_approvals')...")
    try:
        payload = json.dumps({
            "name": "list_pending_approvals",
            "arguments": {}
        }).encode("utf-8")

        req = urllib.request.Request(f"{MCP_URL}/tools/call", data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print("✓ Tool Execution Successful!")
            print(f"   Response Payload: {json.dumps(data.get('result', {}), indent=2)}")
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.read().decode('utf-8')}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Tool Call Error: {e}")
        sys.exit(1)

    print("\n🎉 MCP Server Verification Passed 100% Cleanly!")


if __name__ == "__main__":
    main()
