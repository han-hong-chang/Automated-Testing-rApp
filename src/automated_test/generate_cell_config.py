import json
import sys
from automated_test.convert_cell_coordinates import process_cell_xy_coordinates
import os
import copy
from automated_test.generate_rictest_config  import update_rictest_config

# Template to fill UE settings into
RIC_TEST_CELL_BASE_TEMPLATE = {
    "name": "Micro Cell",
    "band": "n66",
    "areas": "s1,s2",
    "cellsConfig": [
        {
            "cell_number": "C1",
            "arf": "Isotropic-Urban-micro",
            "atm": "7:3",
            "energy_profile": "n66_micro",
            "power": 47,
            "height": 10,
            "azimuth": 0,
            "tilt": 15
        }
    ]
}

# Function: Load the user-provided cell configuration template
def load_cell_config():
    try:
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to the config directory
        config_dir = os.path.join(current_dir, '..', 'config')
        # Construct the full path to the input JSON file
        file_path = os.path.join(config_dir, 'input_cell_config.json')

        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading configuration file: {e}")
        sys.exit(1)
# Function: Process each cell configuration and generate cell profiles
def generate_cell_profiles(cell_configurations):
    cell_profiles = []  # This will store the formatted cell profiles
    positions = []      # This will store the x, y coordinates of each cell

    # Iterate through each cell configuration
    for cell in cell_configurations.get("Cell_Config", []):
        cell_type_name = cell.get("Cell Type Name")  # From user config
        band = cell.get("band5G")                    # From user config
        cells_config = cell.get("cellsConfig", [])[0] # Using the first cellsConfig configuration

        area_names = []

        # Extract site name and x/y positions for each coordinate entry
        for pos in cell.get("cellsCoordinate", []):
            site_name = pos["name"]       # From user config
            area_names.append(site_name)

            positions.append({
                "name": site_name,        # From user config
                "x": pos["x"],            # From user config
                "y": pos["y"]             # From user config
            })

        # Join all area names into a single comma-separated string
        areas = ",".join(area_names)

        # Determine whether the cell type is macro or micro
        if 'macro' in cell_type_name.lower():
            arf = "Isotropic-Urban-macro"
            energy_profile = f"NR-342W"
        else:
            arf = "Isotropic-Urban-micro"
            energy_profile = f"NR-60W"

        # Create a copy of the base template and update it with the cell-specific values
        profile = copy.deepcopy(RIC_TEST_CELL_BASE_TEMPLATE)
        profile["name"] = cell_type_name
        profile["band"] = band
        profile["areas"] = areas
        profile["cellsConfig"][0]["arf"] = arf
        profile["cellsConfig"][0]["energy_profile"] = energy_profile
        profile["cellsConfig"][0]["atm"] = cells_config.get("Advanced traffic model")
        profile["cellsConfig"][0]["power"] = cells_config.get("Configured Tx Power")
        profile["cellsConfig"][0]["height"] = cells_config.get("Height")
        profile["cellsConfig"][0]["azimuth"] = cells_config.get("Azimuth")
        profile["cellsConfig"][0]["tilt"] = cells_config.get("Tilt")

        cell_profiles.append(profile)

    return cell_profiles, positions
# Function: Calculate and return the total number of cells
def calculate_total_number_of_cells(data):
    return sum(cell.get("Number of Cells", 0) for cell in data.get("Cell_Config", []))

# Function: Update the RICTest configuration file with the new cell profiles

