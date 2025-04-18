import subprocess
import os

def start_simulation(config_filename="updated_RIC_Test_v2.4.conf", config_dir="config"):
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