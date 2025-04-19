import subprocess
import os
import requests
import json

def start_rictest_simulation(config_filename="updated_RIC_Test_v2.4.conf", config_dir="config"):
    # Change directory to the parent folder to ensure the 'config' folder is found

    config_path = os.path.join(config_dir, config_filename)

    if not os.path.exists(config_path):
        print(f"Config file '{config_path}' not found.")
        return None

    try:
        result = subprocess.run(
            ["sudo", "curl", "-s", "-o", "response.json", "-w", "%{http_code}",
             "-X", "POST", "http://192.168.8.28:32441/sba/tests/run",
             "-H", "accept: application/json", "-H", "Content-Type: application/json",
             "-d", f"@{config_path}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        status_code = result.stdout.strip()
        print(f"HTTP Status Code: {status_code}")

        if result.stderr:
            print(f"Error output: {result.stderr}")

        return status_code
    except Exception as e:
        print(f"Failed to run SBA test: {e}")
        return None
    
    
    import requests

def stop_rictest_simulation():
    try:
        json_path = os.path.join(os.getcwd(), "response.json")

        # Open and read the response.json file
        with open(json_path, 'r') as f:
            data = json.load(f)

        # Get the test ID from the JSON file
        test_id = data.get("id")
        if not test_id:
            return "⚠️ 'id' not found in JSON."  # If no 'id' found, return a warning message

        # Construct the URL for the DELETE request
        url = f"http://192.168.8.28:32441/sba/tests/status/{test_id}"
        
        # Send the DELETE request to stop the RIC test
        r = requests.delete(url)

        # Return a success or failure message based on the response status
        return f"Stopping RIC Test Simulation with Test ID: {test_id} - {'Stopped' if r.ok else f'Failed ({r.status_code})'}"

    except Exception as e:
        # Catch and return any errors that occur during the process
        return f"❌ Error: {e}"
