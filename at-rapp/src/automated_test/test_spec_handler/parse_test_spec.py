import json
import os

def parse_test_spec():
    # Determine current directory and build paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join("config", "test_spec.json")
    output_dir = os.path.normpath(os.path.join(current_dir, "..", "ric_test_config_generator", "temp_json"))
    os.makedirs(output_dir, exist_ok=True)

    # Load the input test specification JSON
    with open(file_path, "r") as f:
        data = json.load(f)

    cell_index = 1  # Counter for naming cell coordinates
    result_cell_config = {"Cell_Config": []}
    result_ue_config = {"UE_Config": []}
    result_gnb_config = {"gNB_Config": []}

    # Iterate through each configuration in the metadata
    for config in data.get("testMetadata", {}).get("configurationParameters", []):
        # Handle legacy deploymentScale config
        if "deploymentScale" in config:
            ds = config.get("deploymentScale", "macro")
            cell_type_name = "Macro Cell" if ds == "macro" else "Micro Cell"

            num_cells = config.get("numberOfCells", 0)
            band = config.get("band5G", [None])[0]
            power = config.get("totalTransmitPowerIntoAntenna")
            azimuth = config.get("azimuth")
            tilt = config.get("tilt")
            height = config.get("height")
            ratio = config.get("tddDlUlRatio", "")
            coordinates = []

            # Build coordinate list
            for geo in config.get("geoLocGrp", []):
                coordinates.append({
                    "name": f"s{cell_index}",
                    "x": geo.get("longitude"),
                    "y": geo.get("latitude")
                })
                cell_index += 1

            # Append cell configuration entry
            result_cell_config["Cell_Config"].append({
                "Cell Type Name": cell_type_name,
                "Number of Cells": num_cells,
                "band5G": band,
                "cellsConfig": [{
                    "Configured Tx Power": power,
                    "Height": height,
                    "Azimuth": azimuth,
                    "Tilt": tilt,
                    "Advanced traffic model": ratio
                }],
                "cellsCoordinate": coordinates
            })

        # Handle new gNB Config structure
        elif "gNB Config" in config:
            result_gnb_config["gNB_Config"].append(config["gNB Config"])

        # Skip unknown or unexpected config formats
        else:
            print(f"⚠️ Skipping unrecognized config structure: {list(config.keys())}", flush=True)

    # Extract UE context if available
    ue_ctx = data.get("testMetadata", {}) \
                 .get("additionalContext", {}) \
                 .get("ueContexts", [])
    for ue in ue_ctx:
        result_ue_config["UE_Config"].append({
            "numberOfUE": ue.get("numberOfUE", 0),
            "location": ue.get("location", ""),
            "slice": ue.get("slice", ""),
            "targetThroughput": ue.get("targetThroughput", 0),
            "5QI": ue.get("qosId", 1),
            "mobilityModel": ue.get("mobilityModel", ""),
            "mobilitySpeed": ue.get("mobilitySpeed", 0)
        })

    # Output the constructed JSON data to files
    with open(os.path.join(output_dir, "input_cell_config.json"), "w") as f:
        json.dump(result_cell_config, f, indent=2)
    with open(os.path.join(output_dir, "input_ue_config.json"), "w") as f:
        json.dump(result_ue_config, f, indent=2)
    if result_gnb_config["gNB_Config"]:
        with open(os.path.join(output_dir, "input_gnb_config.json"), "w") as f:
            json.dump(result_gnb_config, f, indent=2)

    print("✅ parse_test_spec completed and output JSON files.", flush=True)
