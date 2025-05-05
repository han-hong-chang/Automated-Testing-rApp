import json
import os

def parse_test_spec():
    # Path settings
    current_dir = os.path.dirname(os.path.abspath(__file__))

    file_path = os.path.join("config", "test_spec.json")
    output_dir = os.path.normpath(os.path.join(current_dir, "..", "ric_test_config_generator", "temp_json"))

    # Create the directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Open and read the JSON file
    with open(file_path, "r") as f:
        data = json.load(f)

    # Result for Cell_Config and UE_Config
    cell_index = 1
    result_cell_config = {
        "Cell_Config": []
    }

    result_ue_config = {
        "UE_Config": []
    }

    # Iterate through each configuration in the test metadata
    for config in data["testMetadata"]["configurationParameters"]:
        # Determine the cell type based on the deployment scale
        cell_type_name = "Macro Cell" if config["deploymentScale"] == "macro" else "Micro Cell"
        num_cells = config["numberOfCells"]
        band = config["band5G"][0]
        power = config["totalTransmitPowerIntoAntenna"]
        azimuth = config["azimuth"]
        tilt = config["tilt"]
        height = config["height"]
        ratio = config["tddDlUlRatio"]
        coordinates = []

        # Loop through geographic locations and add coordinates
        for geo in config["geoLocGrp"]:
            coord = {
                "name": f"s{cell_index}",
                "x": geo["longitude"],
                "y": geo["latitude"]
            }
            coordinates.append(coord)
            cell_index += 1

        # Create a cell configuration entry
        cell_config = {
            "Cell Type Name": cell_type_name,
            "Number of Cells": num_cells,
            "band5G": band,
            "cellsConfig": [
                {
                    "Configured Tx Power": power,
                    "Height": height,
                    "Azimuth": azimuth,
                    "Tilt": tilt,
                    "Advanced traffic model": ratio
                }
            ],
            "cellsCoordinate": coordinates
        }

        result_cell_config["Cell_Config"].append(cell_config)

    # Extract ueContext from testMetadata.additionalContext
    ue_ctx = data.get("testMetadata", {}).get("additionalContext", {}).get("ueContext", {})

    if ue_ctx:
        result_ue_config["UE_Config"].append({
            "numberOfUE": ue_ctx.get("numberOfUE", 0),
            "location": ue_ctx.get("location", "s1"),
            "slice": ue_ctx.get("slice", "eMBB"),
            "targetThroughput": ue_ctx.get("targetThroughput", 0),
            "5QI": ue_ctx.get("qosId", 1),
            "mobilityModel": ue_ctx.get("mobilityModel", "stationary"),
            "mobilitySpeed": ue_ctx.get("mobilitySpeed", 0)
        })

    # Output the Cell Config JSON to the specified directory
    with open(os.path.join(output_dir, "input_cell_config.json"), "w") as f:
        json.dump(result_cell_config, f, indent=2)

    # Output the UE Config JSON to the specified directory
    with open(os.path.join(output_dir, "input_ue_config.json"), "w") as f:
        json.dump(result_ue_config, f, indent=2)

def main():
    print("Parsing test_spec.json and generating config files...")
    parse_test_spec()
    print("Done! Check the 'temp_json' folder for output.")

if __name__ == "__main__":
    main()
