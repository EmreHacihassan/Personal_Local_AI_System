
import requests
import sys

def test_endpoint(port, name):
    url = f"http://127.0.0.1:{port}/api/notes/graph"
    print(f"Testing {name} at {url}...")
    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS: Graph endpoint is reachable!")
            print(f"Response data keys: {response.json().keys()}")
        else:
            print(f"FAILURE: {response.text}")
    except Exception as e:
        print(f"ERROR: Could not connect to {name}: {e}")

if __name__ == "__main__":
    print("--- VERIFICATION ---")
    
    # Test Isolation Server
    test_endpoint(8001, "Test Server")
    
    print("\n")
    
    # Test Main Server
    test_endpoint(8000, "Main Server")
