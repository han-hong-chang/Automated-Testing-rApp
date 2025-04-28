import requests
import json
import os
def query_test_spec(
    base_url="http://192.168.8.111:8000",
    subnetwork_id="joetest",
    output_filename="test_spec.json"
):
    """
    Queries the test specification for a given SubNetwork and saves it as a JSON file.
    """
    url = f"{base_url}/ProvMnS/v1alpha1/SubNetwork/{subnetwork_id}"
    headers = {"accept": "application/json"}

    try:
        # Send GET request to the specified URL
        response = requests.get(url, headers=headers)
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return

    if response.status_code == 200:
        try:
            # Automatically get the current path and save to ./config directory
            config_dir = os.path.join(os.getcwd(), "config")
            os.makedirs(config_dir, exist_ok=True)  # Create directory if it doesn't exist
            output_path = os.path.join(config_dir, output_filename)

            # Write the JSON response to a file
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(response.json(), f, indent=2, ensure_ascii=False)
            print(f"✅ Successfully saved JSON to: {output_path}")
            return response.json()

        except Exception as e:
            print(f"❌ Failed to write JSON file: {e}")
    else:
        print(f"❌ Error, HTTP status code {response.status_code}")
        print("Response content:", response.text)
