import json
import sys
import os
import copy
from automated_test.ric_test_config_generator.generate_rictest_config  import update_rictest_config
# Template to fill UE settings into
RIC_TEST_UE_BASE_TEMPLATE = {
    "global-id": "slice-default-{ue}",
    "Description": "default slice for the UE",
    "device_model": "SISO-1-0-1-Maximum",
    "serviceConfig": [
        {
            "qosId": 1,
            "slice": "eMBB",
            "targetTput": 0.028,
            "gbrTput": 0,
            "initial_call_state": "Active",
            "Average time between calls": 0,
            "Average call duration": 1,
            "timer_randomness": "Poisson"
        }
    ],
    "seed": "0x7e5",
    "ueHeight": 1.5,
    "distribution": [
        {
            "ues": 5,
            "locations": "s1"
        }
    ],
    "mobility": {
        "type": "short range",
        "speed": 1.5,
        "roundtrip": "return",
    }
}

# Load input UE config
# Load input UE config
def load_ue_config():
    """
    Load UE configuration from a specified JSON file.
    
    This function attempts to read and parse a configuration file for UE settings.
    If the file cannot be found or read, it will terminate the program with an error.
    
    Returns:
        dict: The parsed UE configuration data.
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(current_dir, '..', '..', 'config')
        file_path = os.path.join(config_dir, 'input_ue_config.json')  # Path to UE config file

        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"❌ Error loading UE configuration file: {e}")
        sys.exit(1)

# Convert each UE config into full profile config
def generate_ue_profiles(ue_configurations):
    """
    Load UE configuration and generate a complete profile configuration.
    
    This function loads the configuration from the file and generates a full configuration
    for each UE based on the predefined base template, filling in the appropriate values.
    
    Returns:
        list: A list of complete UE profiles with the appropriate settings applied.
    """
    ue_data = load_ue_config()
    ue_configurations = ue_data.get("UE_Config", [])

    ue_profiles = []
    for idx, ue in enumerate(ue_configurations):
        profile = copy.deepcopy(RIC_TEST_UE_BASE_TEMPLATE)

        # ➤ Original mobilityModel name (default to "walking" if not specified)
        original_model = ue.get("mobilityModel", "walking")

        # ➤ global-id used as model_ue-{index}
        profile["global-id"] = f"{original_model}_ue-{idx+1}"

        # ➤ Description based on mobilityModel
        profile["Description"] = f"{original_model} UE"

        # ➤ Set mobility type to "short range"
        profile["mobility"]["type"] = "short range"
        profile["mobility"]["speed"] = ue.get("mobilitySpeed", 1.5)  # Default speed is 1.5 if not provided

        # ➤ UE distribution settings
        profile["distribution"][0]["locations"] = ue.get("location", "s1")  # Default location is "s1"
        profile["distribution"][0]["ues"] = ue.get("numberOfUE", 5)  # Default number of UEs is 5

        # ➤ Service configuration settings
        profile["serviceConfig"][0]["slice"] = ue.get("slice", "default")
        profile["serviceConfig"][0]["qosId"] = ue.get("5QI", 4)  # Default QoS ID is 4
        profile["serviceConfig"][0]["targetTput"] = ue.get("targetThroughput", 0.2)  # Default throughput is 0.2

        ue_profiles.append(profile)

    return ue_profiles
