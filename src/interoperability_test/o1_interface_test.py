import subprocess
import json
import time
from ncclient import manager
import logging
import re
import os
# Configure logger


# Function: Read JSON and check if 'smo.o1' is listed in interfaceUnderTest
def get_test_interfaces():
    json_path = os.path.join("config", "test_spec.json")

    with open(json_path, 'r') as f:
        data = json.load(f)

    # Extract interface names (converted to lowercase for consistency)
    interfaces = data.get("testMetadata", {}).get("interfaceUnderTest", [])
    interface_names = [iface.lower() for iface in interfaces]

    print(f"Start interface interoperability test with interfaces: {', '.join(interface_names)}")

    return interface_names
# Function: Test NETCONF connection
def test_o1_netconf_connection():
    try:
        with manager.connect(
            host="192.168.8.28",
            port=31677,
            username="root",
            password="viavi",
            hostkey_verify=False
        ) as m:
            print("Connected to NETCONF server successfully.")
            return True
    except Exception as e:
        print(f"Failed to connect to NETCONF server: {str(e)}")
        return False

# Function: Monitor logs for VES sourceId and get pod name
def test_o1_ves_connection(target_source_id, check_interval=10, timeout=60):
    namespace = "o1ves"
    pod_name = "o1ves-common-dmaap-influxdb"

    try:
        # ... Omitted the pod_name fetching part ...

        # Step 2: Monitor logs for SourceId in the selected pod
        print(f"Starting log monitoring for SourceId: {target_source_id} in pod '{pod_name}'...")
        process = subprocess.Popen(
            ["sudo", "kubectl", "logs", "-n", namespace, pod_name, "--tail=0", "-f"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        start_time = time.time()

        while True:
            print("Checking O1 VES connection status...")  # Log before each check

            logs = process.stdout.readline()
            if logs:
                source_ids = re.findall(r'"sourceId":"([^"]*)"', logs)
                if target_source_id in source_ids:
                    print(f"✅ VES Test Passed: Found SourceId {target_source_id}")
                    process.terminate()
                    process.wait()
                    return True

            # Check if timeout is reached
            if time.time() - start_time > timeout:
                print("❌ VES Test Failed: Timeout reached without finding the target SourceId.")
                process.terminate()
                process.wait()
                return False

            time.sleep(check_interval)  # Wait for the specified interval before next check

    except Exception as e:
        print(f"⚠️ Error during log monitoring: {e}")
        return False
