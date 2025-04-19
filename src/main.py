import json
import os
import time

from automated_test.generate_cell_config import (
    load_cell_config,
    generate_cell_profiles,
    calculate_total_number_of_cells
)
from automated_test.generate_ue_config import (
    load_ue_config,
    generate_ue_profiles
)
from automated_test.generate_rictest_config import update_rictest_config
from automated_test.convert_cell_coordinates import process_cell_xy_coordinates
from automated_test.rictest_controller import (
    start_rictest_simulation,
    stop_rictest_simulation
)
from interoperability_test.o1_interface_test import (
    get_interface_and_vendor,
    test_o1_netconf_connection,
    test_o1_ves_connection
    
)

def main():

    # Step 1: Load user configuration
    # Load cell configuration from file
    cell_data = load_cell_config()
    # Load UE configuration from file
    ue_data = load_ue_config()

    # Step 2: Generate cell profiles and coordinates
    # Generate cell profiles and positions based on the loaded cell configuration
    cell_profiles, positions = generate_cell_profiles(cell_data)
    # Generate UE profiles based on the loaded UE configuration
    ue_profiles = generate_ue_profiles(ue_data)

    # Step 3: Output cell profiles and coordinates to JSON files
    # Write the generated cell profiles to a JSON file (in RIC Test format)
    with open(os.path.join("automated_test", "temp_json", "output_cell_config.json"), "w") as posfile:
        json.dump(cell_profiles, posfile, indent=4)

    with open(os.path.join("automated_test", "temp_json", "cell_positions.json"), "w") as posfile:
        json.dump({"cells": positions}, posfile, indent=4)
    # Step 4: Calculate the total number of cells
    # Calculate the total number of cells based on the configuration data
    total_number_of_cells = calculate_total_number_of_cells(cell_data)
    print(f"Total number of cells: {total_number_of_cells}")

    # Set the output file path for storing the converted XY coordinates
    output_file = os.path.join("automated_test","temp_json", "converted_xy_coordinates.json")
    
    # Process the cell positions and convert them to relative coordinates
    # This step moves all XY positions to a relative position and generates output coordinates
    reference_distance, output_string = process_cell_xy_coordinates(
        os.path.join("automated_test","temp_json", "cell_positions.json"), 
        output_file
    )

    # Display the results or an error message if processing fails
    if reference_distance is not None:
        print(f"Reference Distance: {reference_distance}")
        print(f"Generated Coordinates: {output_string}")
    else:
        print("Processing failed!")

    # Step 5: Update the RIC Test configuration file
    # Use the generated cell and UE profiles along with the total number of cells to update the RIC Test configuration
    update_rictest_config(
        cell_profiles, 
        ue_profiles, 
        total_number_of_cells, 
        'RIC_Test_v2.4.conf', 
        reference_distance, 
        output_string
    )
    simulation_response = start_rictest_simulation(config_filename="updated_RIC_Test_v2.4.conf", config_dir="config")
    
    if simulation_response:
        print(f"Simulation started, HTTP Status Code: {simulation_response}")
    else:
        print("Simulation failed to start.")
        
    ## Interface interoperabbility test
    print("Start interface interoperabbility test")
    json_path = "test-spec.json"
    # Step 1: Check if smo.o1 is listed in interfaceUnderTest
    need_test, vendor_name = get_interface_and_vendor(json_path)
    if not need_test:
        print("Skipping NETCONF and VES tests.")
        return

    # Step 2: Test NETCONF connection
    netconf_success = test_o1_netconf_connection()
    netconf_result = "Pass" if netconf_success else "Failed"


    # Step 3: Test VES connection
    target_source_id = f"{vendor_name}-RIC-Test" if vendor_name else "Unknown-RIC-Test"
    ves_success = test_o1_ves_connection(vendor_name, target_source_id)
    ves_result = "Pass" if ves_success else "Failed"

    # Final output for both tests
    print(f"O1 Netconf: {netconf_result}")
    print(f"O1 VES: {ves_result}")
    time.sleep(10)
    stop_result = stop_rictest_simulation()
    print(stop_result)
if __name__ == "__main__":
    main()
