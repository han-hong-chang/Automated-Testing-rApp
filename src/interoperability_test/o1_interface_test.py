import subprocess
import json
import time
from ncclient import manager
import logging
import re
import os
# Configure logger


# Function: Read JSON and check if 'smo.o1' is listed in interfaceUnderTest
def get_interfaces_and_vendor():
    json_path = os.path.join("config", "test_spec.json")

    with open(json_path, 'r') as f:
        data = json.load(f)

    # Extract interface names (converted to lowercase for consistency)
    interfaces = data.get("testMetadata", {}).get("interfaceUnderTest", [])
    interface_names = [iface.lower() for iface in interfaces]

    # Extract vendor/manufacturer name from testbedComponents
    components = data.get("testbedComponents", [])
    vendor_name = components[0].get("manufacturerName") if components else None
    print(f"Start interface interoperability test with interfaces: {', '.join(interface_names)} and vendor: {vendor_name}")

    return interface_names, vendor_name
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
def test_o1_ves_connection(vendor_name, target_source_id, check_interval=10, timeout=100):
    namespace = "o1ves"
    pattern = "o1ves-dmaap-influxdb-adapter"

    try:
        # Step 1: Get the pod name dynamically
        result = subprocess.run(
            ["sudo", "kubectl", "get", "pods", "-n", namespace],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        
        pod_name = None
        for line in result.stdout.splitlines():
            if pattern in line:
                pod_name = line.split()[0]
                break

        if not pod_name:
            print("Pod not found. Skipping VES test.")
            return False

        # Step 2: Monitor logs for SourceId in the selected pod
        print(f"Starting log monitoring for SourceId: {target_source_id} in pod '{pod_name}'...")
        process = subprocess.Popen(
            ["sudo", "kubectl", "logs", "-n", namespace, pod_name, "--tail=0", "-f"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        start_time = time.time()

        while True:
            logs = process.stdout.readline()
            if logs:
                source_ids = re.findall(r'"sourceId":"([^"]*)"', logs)
                if target_source_id in source_ids:
                    print(f"VES Test Passed: Found SourceId {target_source_id}")
                    return True  # Return True when sourceId is found

            if time.time() - start_time > timeout:
                print("VES Test Failed: Timeout reached without finding the target sourceId.")
                return False  # Return False if timeout is reached

            print(f"Waiting for VES event from {vendor_name}...")
            time.sleep(check_interval)

        process.terminate()
        process.wait()

    except Exception as e:
        print(f"Error during log monitoring: {e}")
        return False  # Return False if there's an exception

