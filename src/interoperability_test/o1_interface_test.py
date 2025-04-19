import subprocess
import json
import time
from ncclient import manager
import logging
import re

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function: Read JSON and check if 'smo.o1' is listed in interfaceUnderTest
def get_interface_and_vendor(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)

    interfaces = data.get("testMetadata", {}).get("interfaceUnderTest", [])
    vendor_name = None

    components = data.get("testbedComponents", [])
    if components and "manufacturerName" in components[0]:
        vendor_name = components[0]["manufacturerName"]

    return "smo.o1" in interfaces, vendor_name

# Function: Test NETCONF connection
def test_o1_netconf_connection():
    try:
        with manager.connect(
            host="192.168.8.28",
            port=30901,
            username="root",
            password="viavi",
            hostkey_verify=False
        ) as m:
            logger.info("Connected to NETCONF server successfully.")
            return True
    except Exception as e:
        logger.error(f"Failed to connect to NETCONF server: {str(e)}")
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

# Main process
def main():
    json_path = "test-spec.json"
    # Step 1: Check if smo.o1 is listed in interfaceUnderTest
    need_test, vendor_name = get_interface_and_vendor(json_path)
    if not need_test:
        print("Skipping NETCONF and VES tests.")
        return

    # Step 2: Test NETCONF connection
    netconf_success = test_o1_netconf_connection()
    netconf_result = "Pass" if netconf_success else "Failed"
    if not netconf_success:
        print("O1 Netconf: Failed")

    # Step 3: Test VES connection
    target_source_id = f"{vendor_name}-RIC-Test" if vendor_name else "Unknown-RIC-Test"
    ves_success = test_o1_ves_connection(vendor_name, target_source_id)
    ves_result = "Pass" if ves_success else "Failed"

    # Final output for both tests
    print(f"O1 Netconf: {netconf_result}")
    print(f"O1 VES: {ves_result}")

if __name__ == "__main__":
    main()

