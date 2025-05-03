import requests
import json
import sys

def test_connection():
    """Test basic connection to the MCP server."""
    try:
        response = requests.get("http://localhost:8080/list_tools")
        if response.status_code == 200:
            data = response.json()
            print("Successfully connected to MCP server!")
            print(f"Available tools: {len(data['tools'])}")
            for tool in data['tools']:
                print(f"- {tool['name']}: {tool['description']}")
            return True
        else:
            print(f"Error: Received status code {response.status_code}")
            print(response.text)
            return False
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the MCP server at http://localhost:8080")
        print("Make sure the server is running with: python main.py serve")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_analyze_code():
    """Test the analyze_code tool."""
    try:
        payload = {
            "name": "analyze_code",
            "arguments": {
                "code": "def hello():\n    print('Hello, world!')",
                "language": "python",
                "pattern": "def $FUNC_NAME()"
            }
        }
        
        response = requests.post(
            "http://localhost:8080/call_tool",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\nAnalyze code test:")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"Error: Received status code {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing MCP server connection...")
    if test_connection():
        test_analyze_code()
    else:
        sys.exit(1) 