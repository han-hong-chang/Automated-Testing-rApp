import json
import sys
import os

def update_rictest_config(cell_profiles, filled_ue_config, total_number_of_cells, config_file_path, reference_distance=None, output_string=None):
    try:
        # Get the directory of the current script (the directory where this script is located)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Construct the path to the config directory (relative to the current script)
        config_dir = os.path.join(current_dir, '..', '..', 'config')  # Adjust the relative path to 'config'
        
        # Combine the config directory and the config file path to form the full file path
        full_config_file_path = os.path.join(config_dir, config_file_path)

        # Open and read the config file
        with open(full_config_file_path, 'r') as conf_file:
            conf_data = json.load(conf_file)

        # ✅ Update number
        if "config" in conf_data and "Scenario_Generation" in conf_data["config"]:
            conf_data["config"]["Scenario_Generation"]["map"]["number"] = total_number_of_cells

            # ✅ If there is a distribution field
            if "distribution" in conf_data["config"]["Scenario_Generation"]["map"]:
                if reference_distance is not None:
                    conf_data["config"]["Scenario_Generation"]["map"]["distribution"]["distance"] = reference_distance
                if output_string is not None:
                    # ❗ Directly overwrite the entire diagram, no need for "" as your output already contains the full format
                    conf_data["config"]["Scenario_Generation"]["map"]["distribution"]["diagram"] = output_string
        else:
            raise ValueError("The 'Scenario_Generation' or 'map' structure is missing in the config.")

        # ✅ Update Cell_Profiles
        if "config" in conf_data and "Cells" in conf_data["config"]:
            conf_data["config"]["Cells"]["Cell_Profiles"] = cell_profiles
        else:
            raise ValueError("The 'Cells' structure is missing in the config.")
        
        # ✅ Update UE_Groups section with the final UE config
        if "config" in conf_data and "UE_Configuration" in conf_data["config"] and "UE_Groups" in conf_data["config"]["UE_Configuration"]:
            conf_data["config"]["UE_Configuration"]["UE_Groups"] = filled_ue_config
        else:
            raise ValueError("The 'UE_Groups' structure is missing in the RIC Test config under 'config -> UE_Configuration'.")

        # ✅ Save the updated config back to the 'config' directory with a new name (or the same name)
        updated_config_file_path = os.path.join(config_dir, "updated_" + os.path.basename(config_file_path))
        
        with open(updated_config_file_path, 'w') as conf_file:
            json.dump(conf_data, conf_file, indent=4)


        # Load the updated configuration file and print it
        with open(updated_config_file_path, 'r') as updated_file:
            updated_config = json.load(updated_file)
        
        # Print the updated configuration
        print("Updated RIC Test Configuration:")
        print(json.dumps(updated_config, indent=4))  # Pretty-print the updated config
        print(f"✅ Successfully updated RIC Test configuration file and saved to {updated_config_file_path}")

    except json.JSONDecodeError as e:
        print(f"❌ JSON format error: {e.msg} at line {e.lineno} column {e.colno}")
        sys.exit(1)

    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
