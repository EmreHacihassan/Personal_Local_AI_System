
import requests
import json
import time

def verify_production():
    url = "http://127.0.0.1:8000/api/notes/graph"
    print(f"Verifying production endpoint: {url}")
    
    # Try a few times in case server is still starting
    for i in range(5):
        try:
            response = requests.get(url, timeout=5)
            print(f"Attempt {i+1}: Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                node_count = len(data.get("nodes", []))
                edge_count = len(data.get("edges", []))
                print(f"SUCCESS: Graph loaded with {node_count} nodes and {edge_count} edges.")
                return True
            else:
                print(f"FAILURE: Server returned {response.status_code}")
                # Print first 100 chars of response to see error
                print(f"Response: {response.text[:100]}")
                
        except Exception as e:
            print(f"Attempt {i+1} failed: {e}")
        
        time.sleep(2)
    
    return False

if __name__ == "__main__":
    verify_production()
